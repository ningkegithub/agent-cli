#!/usr/bin/env python3
import sys
import os
import asyncio
from dotenv import load_dotenv

# 加载环境变量 (必须在导入其他模块前执行)
load_dotenv()

import time
import threading
import queue
import signal
import subprocess
import atexit

# Rich & PromptToolkit
from rich.live import Live
from rich.text import Text
from rich.markup import escape
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

# 核心依赖
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from agent_core import build_graph
from agent_core.nodes import shutdown_llm_clients

# 本地模块
from cli.config import console, check_api_key, get_random_phrase
from cli.async_worker import run_worker
import cli.ui as ui

_LAST_CHAT_HISTORY = None
_LAST_STOP_EVENT = None
_LAST_WORKER_THREAD = None
_ARCHIVE_ON_EXIT_DONE = False

def _msg_key(msg):
    """生成消息去重键：优先使用消息 id，缺失时回退到对象地址。"""
    msg_id = getattr(msg, "id", None)
    if msg_id:
        return f"id:{msg_id}"
    # 注意：部分消息可能没有 id，避免 None 造成全量去重
    return f"obj:{id(msg)}"

def _maybe_trim_prefix(text: str, trim_prefix: str) -> tuple[str, str]:
    """如果新内容重复旧前缀，则在显示时裁剪该前缀。"""
    if not trim_prefix or not text:
        return text, trim_prefix
    # 前缀还没完整到达，先不显示，避免重复闪现
    if trim_prefix.startswith(text):
        return "", trim_prefix
    # 新内容包含旧前缀，裁剪掉
    if text.startswith(trim_prefix):
        return text[len(trim_prefix):].lstrip(), ""
    # 无匹配则直接显示并清除前缀
    return text, ""

def _render_live(live, accumulated_content: str, spinner_text: Text | None):
    """更新 Live 视图（单区）。"""
    if accumulated_content:
        live.update(Markdown(f"**AI >** {accumulated_content}"))
    else:
        live.update(spinner_text or Text(""))

def _flush_live_snapshot(live, accumulated_content: str):
    """将当前 Live 内容固化为持久输出，避免被清屏覆盖。"""
    if not accumulated_content:
        return
    live.update(Text(""))
    live.refresh()
    live.stop()
    console.print(Markdown(f"**AI >** {accumulated_content}"))

def _archive_session(chat_history):
    """将当前会话历史归档为 Markdown 文件"""
    if not chat_history: return
    
    import datetime
    import os
    from agent_core.utils import USER_MEMORY_DIR
    
    logs_dir = os.path.join(USER_MEMORY_DIR, "logs")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # 按日期归档
    target_dir = os.path.join(logs_dir, today)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
    # 文件名包含日期和时间，更加清晰且唯一
    filename = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_session.md"
    file_path = os.path.join(target_dir, filename)
    
    content = [f"# Session Log: {datetime.datetime.now()}"]
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            role = "User"
        elif isinstance(msg, AIMessage):
            role = "AI"
        elif isinstance(msg, ToolMessage):
            role = "Tool"
        else:
            role = "System"
            
        text = str(msg.content)
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                text += f"\n\n🛠️ Call: {tc['name']}({tc['args']})"
                
        content.append(f"\n## {role}\n{text}")
        
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        console.print(f"[dim]💾 会话已归档至: .../logs/{today}/{filename}[/dim]")
        
        # [新增] 自动入库到 episodic_memory
        # 使用 subprocess 调用 ingest.py，确保环境隔离且路径正确
        # 假设 ingest.py 在标准位置
        ingest_script = os.path.join(os.getcwd(), "skills/knowledge_base/scripts/ingest.py")
        if os.path.exists(ingest_script):
            # 使用 sys.executable 确保使用当前的 venv python
            # 传入 file_path 和 collection_name="episodic_memory"
            # 无论成功与否，不应阻塞退出，所以 capture_output=True 且不 check
            proc = subprocess.run(
                [sys.executable, ingest_script, file_path, "episodic_memory"],
                capture_output=True,
                text=True
            )
            if proc.returncode == 0:
                console.print(f"[dim]🧠 记忆已同步至 episodic_memory[/dim]")
            else:
                err_text = (proc.stderr or proc.stdout or "").strip()
                err_line = err_text.splitlines()[0] if err_text else ""
                suffix = f" {err_line[:200]}" if err_line else ""
                console.print(f"[dim]⚠️ 记忆同步失败 (code {proc.returncode}){suffix}[/dim]")
        else:
            console.print(f"[dim]⚠️ 未找到 ingest 脚本，跳过记忆同步[/dim]")
            
    except Exception as e:
        console.print(f"[red]归档失败: {e}[/red]")

def _archive_session_once(chat_history):
    """退出路径只归档一次，避免重复写入。"""
    global _ARCHIVE_ON_EXIT_DONE
    if _ARCHIVE_ON_EXIT_DONE:
        return
    _ARCHIVE_ON_EXIT_DONE = True
    _archive_session(chat_history)

def _graceful_exit(stop_event, worker_thread, history=None):
    """退出前尽量停止后台线程，并归档会话。"""
    try:
        if history:
            _archive_session_once(history)
            
        if stop_event and worker_thread and worker_thread.is_alive():
            stop_event.set()
            worker_thread.join(timeout=1.0)
        shutdown_llm_clients()
    finally:
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        except Exception:
            pass

def _set_runtime_context(history, stop_event, worker_thread):
    """更新退出时可用的上下文。"""
    global _LAST_CHAT_HISTORY, _LAST_STOP_EVENT, _LAST_WORKER_THREAD
    _LAST_CHAT_HISTORY = history
    _LAST_STOP_EVENT = stop_event
    _LAST_WORKER_THREAD = worker_thread

def _handle_termination(signum, frame):
    """处理 SIGTERM/SIGHUP，尽量归档并退出。"""
    try:
        console.print(f"[dim]⚠️ 收到终止信号 {signum}，正在归档会话并退出...[/dim]")
        _graceful_exit(_LAST_STOP_EVENT, _LAST_WORKER_THREAD, _LAST_CHAT_HISTORY)
    finally:
        raise SystemExit(0)

def _install_exit_handlers():
    """安装退出钩子，覆盖非优雅退出场景。"""
    atexit.register(lambda: _archive_session_once(_LAST_CHAT_HISTORY))
    for sig in ("SIGTERM", "SIGHUP"):
        sig_value = getattr(signal, sig, None)
        if sig_value is not None:
            signal.signal(sig_value, _handle_termination)

def main():
    ui.render_header()
    _install_exit_handlers()
    
    if not check_api_key():
        return

    try:
        app = build_graph()
    except Exception as e:
        ui.render_error(console, f"初始化失败: {e}")
        return
    
    chat_history = []
    active_skills = {}
    
    style = Style.from_dict({'prompt': 'ansigreen bold'})
    session = PromptSession()

    last_interrupt_time = 0.0

    while True:
        stop_event = None
        worker_thread = None
        try:
            print()
            user_input = session.prompt("用户> ", style=style)
            if user_input.lower() in ["exit", "quit"]:
                console.print("[dim]👋 再见！[/dim]")
                _graceful_exit(stop_event, worker_thread, chat_history)
                return
            if not user_input.strip():
                continue

            inputs = {
                "messages": chat_history + [HumanMessage(content=user_input)],
                "active_skills": active_skills
            }
            
            # --- 初始化状态 ---
            current_messages = inputs["messages"]
            accumulated_content = ""
            last_flushed_content = ""
            display_trim_prefix = ""
            seen_message_keys = {_msg_key(msg) for msg in chat_history}
            
            # 线程通信
            output_queue = queue.Queue()
            stop_event = threading.Event()
            worker_thread = threading.Thread(
                target=run_worker, 
                args=(app, inputs, output_queue, stop_event), 
                daemon=True
            )
            worker_thread.start()
            _set_runtime_context(chat_history, stop_event, worker_thread)
            
            # UI 状态
            start_time = time.time()
            last_phrase_update = start_time
            current_phrase = get_random_phrase()
            is_thinking = True
            
            with Live(console=console, refresh_per_second=12, vertical_overflow="visible") as live:
                while True:
                    # 更新状态栏
                    now = time.time()
                    elapsed = now - start_time
                    if now - last_phrase_update > 3.0:
                        current_phrase = get_random_phrase()
                        last_phrase_update = now
                    
                    if is_thinking:
                        spinner_text = ui.get_spinner_text(current_phrase, elapsed)
                        display_content, display_trim_prefix = _maybe_trim_prefix(accumulated_content, display_trim_prefix)
                        _render_live(live, display_content, spinner_text)
                    else:
                        display_content, display_trim_prefix = _maybe_trim_prefix(accumulated_content, display_trim_prefix)
                        _render_live(live, display_content, None)

                    # 消费队列
                    try:
                        msg_type, mode, data = output_queue.get(timeout=0.05)
                        
                        if msg_type == "done": break
                        if msg_type == "error": raise data
                        
                        if msg_type == "stream":
                            if mode == "messages":
                                chunk = data[0]
                                if isinstance(chunk, AIMessageChunk):
                                    if chunk.content:
                                        is_thinking = False # 有字了，停转圈
                                        accumulated_content += chunk.content
                                        display_content, display_trim_prefix = _maybe_trim_prefix(accumulated_content, display_trim_prefix)
                                        _render_live(live, display_content, None)
                                    
                                    if chunk.tool_call_chunks:
                                        tc = chunk.tool_call_chunks[0]
                                        if tc.get("name"):
                                            # 切换状态前，先固化当前流式内容，避免被清屏覆盖
                                            if accumulated_content and accumulated_content != last_flushed_content:
                                                _flush_live_snapshot(live, accumulated_content)
                                                last_flushed_content = accumulated_content
                                                display_trim_prefix = last_flushed_content
                                            live.start() # 清屏
                                            accumulated_content = ""
                                            
                                            safe_name = escape(tc.get("name", "Unknown"))
                                            # 在 Spinner 中显式显示正在准备调用的工具名
                                            current_phrase = f"[bold yellow]⚙️ 准备执行: {safe_name}...[/bold yellow]"
                                            is_thinking = True
                                            _render_live(live, accumulated_content, ui.get_spinner_text(current_phrase, elapsed))

                            elif mode == "updates":
                                for _, node_output in data.items():
                                    if not node_output: continue
                                    
                                    if "active_skills" in node_output:
                                        active_skills = node_output["active_skills"]
                                    
                                    if "messages" in node_output:
                                        for msg in node_output["messages"]:
                                            msg_key = _msg_key(msg)
                                            if msg_key in seen_message_keys: continue
                                            seen_message_keys.add(msg_key)
                                            
                                            # [优化] 跳过 AIMessage 的文本部分，防止与流式输出重复
                                            # 但如果包含工具调用，必须在这里渲染工具卡片（因为 Stream 模式下无法获取完整参数）
                                            if isinstance(msg, AIMessage):
                                                if msg.tool_calls:
                                                    live.update(Text(""))
                                                    live.stop()
                                                    for tc in msg.tool_calls:
                                                        ui.render_tool_action(console, tc['name'], tc['args'])
                                                    live.start()
                                                    is_thinking = True # 工具执行中
                                                
                                                current_messages.append(msg)
                                                continue
                                            
                                            # 展示结果 (ToolMessage)
                                            # 工具结果通常不通过 stream message chunk 发送，或者是整块发送，适合在这里处理
                                            if isinstance(msg, ToolMessage):
                                                live.update(Text(""))
                                                live.stop()
                                                ui.render_tool_result(console, msg.name, msg.content)
                                                live.start()
                                                is_thinking = True
                                                current_phrase = "继续思考..."
                                            
                                            current_messages.append(msg)

                    except queue.Empty:
                        continue

            chat_history = current_messages
            _set_runtime_context(chat_history, stop_event, worker_thread)

        except KeyboardInterrupt:
            now = time.monotonic()
            # 二次 Ctrl+C 直接退出
            if now - last_interrupt_time < 1.5:
                console.print("\n[bold red]👋 已退出[/bold red]")
                _graceful_exit(stop_event, worker_thread, chat_history)
                return
            last_interrupt_time = now

            # 任务中则取消，否则直接退出
            if stop_event and worker_thread and worker_thread.is_alive():
                stop_event.set()
                console.print("\n[bold red]⛔ 用户取消操作 (User Cancelled)[/bold red]")
                time.sleep(0.2)
                continue
            console.print("\n[bold red]👋 已退出[/bold red]")
            _graceful_exit(stop_event, worker_thread, chat_history)
            return
        except Exception as e:
            ui.render_error(console, e)

if __name__ == "__main__":
    main()
