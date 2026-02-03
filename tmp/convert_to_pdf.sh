#!/bin/bash

# 脚本：将 txt 文件转换为 PDF
# 用法：./convert_to_pdf.sh <输入文件> <输出文件>

# 检查参数数量
if [ $# -lt 1 ]; then
    echo "用法: $0 <输入文件> [输出文件]"
    echo "示例: $0 output/我来了.txt"
    echo "示例: $0 output/我来了.txt output/我来了.pdf"
    exit 1
fi

INPUT_FILE="$1"

# 检查输入文件是否存在
if [ ! -f "$INPUT_FILE" ]; then
    echo "错误: 输入文件 '$INPUT_FILE' 不存在"
    exit 1
fi

# 设置输出文件名
if [ $# -ge 2 ]; then
    OUTPUT_FILE="$2"
else
    # 如果没有指定输出文件，使用输入文件名（扩展名改为 .pdf）
    BASENAME=$(basename "$INPUT_FILE" .txt)
    OUTPUT_FILE="output/${BASENAME}.pdf"
fi

# 确保输出目录存在
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "正在转换: $INPUT_FILE -> $OUTPUT_FILE"

# 使用 pandoc 进行转换
pandoc "$INPUT_FILE" -o "$OUTPUT_FILE" \
    --pdf-engine=xelatex \
    -V mainfont="PingFang SC" \
    -V geometry:margin=1in

# 检查转换是否成功
if [ $? -eq 0 ]; then
    echo "转换成功! PDF 文件已保存到: $OUTPUT_FILE"
    echo "文件大小: $(du -h "$OUTPUT_FILE" | cut -f1)"
else
    echo "转换失败，请检查 pandoc 和 LaTeX 环境"
    exit 1
fi