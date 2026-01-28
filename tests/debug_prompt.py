import os

def run():
    skills = {
        "imagetopdf": "这是图片处理协议...",
        "coder": "这是编程专家协议..."
    }
    prompt = "你是一个智能助手。\n当前目录: " + os.getcwd()
    if skills:
        prompt += "\n\n=== 已激活技能 ==="
        for name, content in skills.items():
            prompt += f"\n\n[{name}]\n{content}"
        prompt += "\n==============="
    print(prompt)

if __name__ == "__main__":
    run()

