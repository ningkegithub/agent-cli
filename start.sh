#!/bin/bash
# 强制使用当前目录下的虚拟环境运行 ZX CLI
# 获取脚本所在目录的绝对路径
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查 venv 是否存在
if [ ! -f "$DIR/venv/bin/python3" ]; then
    echo "错误: 未找到虚拟环境，请先运行 'python3 -m venv venv' 并安装依赖。"
    exit 1
fi

# 运行主程序
exec "$DIR/venv/bin/python3" "$DIR/main.py" "$@"
