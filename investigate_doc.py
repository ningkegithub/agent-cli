import docx

file_path = "demo_materials/2_星云科技_产品白皮书_Full.docx"
doc = docx.Document(file_path)

full_text = []
for para in doc.paragraphs:
    full_text.append(para.text)

total_lines = len(full_text)
print(f"📄 文档总段落数 (Lines): {total_lines}")

# 查找关键信息的行号
targets = [
    "KEY FEATURE: Nebula AI supports 10M+ SKU",
    "KEY FEATURE: Built-in DeepSeek-V3",
    "KEY FEATURE: Full On-Premise deployment"
]

print("\n🔍 关键信息位置定位:")
for target in targets:
    found = False
    for i, line in enumerate(full_text):
        if target in line:
            print(f"  - 行号 {i+1}: 找到了 '{target[:30]}...'")
            found = True
            break
    if not found:
        print(f"  - ❌ 未找到 '{target[:30]}...'")

print(f"\n📊 前 100 行是否包含所有信息? {'是' if all(t in '\n'.join(full_text[:100]) for t in targets) else '否'}")

