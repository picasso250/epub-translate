#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from zipfile import ZipFile
import argparse
import re

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='将EPUB文件转换为TXT文件')
    parser.add_argument('-f', '--file', dest='filename', required=True,
                      help='输入的EPUB文件路径')
    parser.add_argument('-o', '--output', dest='output',
                      help='输出的TXT文件路径，默认为[输入文件名].txt')
    return parser.parse_args()

def is_printable(s):
    """检查文本是否可打印"""
    return not any(repr(ch).startswith("'\\x") or repr(ch).startswith("'\\u") for ch in s)

def clean_text(text):
    """清理文本内容"""
    if not text or not is_printable(text):
        return ""
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除特殊字符
    text = text.strip()
    return text

def epub_to_txt(epub_path, txt_path):
    """将EPUB文件转换为TXT文件"""
    print(f"正在处理: {epub_path}")
    
    content = []
    with ZipFile(epub_path, 'r') as zip_file:
        for file_info in zip_file.infolist():
            if file_info.filename.endswith('.html') or file_info.filename.endswith('.xhtml'):
                try:
                    filedata = zip_file.read(file_info.filename)
                    text_data = filedata.decode('utf-8')
                    
                    inside_tag = 0
                    current_text = ""
                    
                    for char in text_data:
                        if char == "<":
                            inside_tag += 1
                            if current_text:
                                cleaned = clean_text(current_text)
                                if cleaned:
                                    content.append(cleaned)
                                current_text = ""
                        elif char == ">":
                            inside_tag -= 1
                        elif inside_tag == 0:
                            current_text += char
                            
                    # 处理最后一段文本
                    if current_text:
                        cleaned = clean_text(current_text)
                        if cleaned:
                            content.append(cleaned)
                            
                except Exception as e:
                    print(f"处理文件 {file_info.filename} 时出错: {str(e)}")
    
    # 将所有内容写入TXT文件
    with open(txt_path, 'w', encoding='utf-8') as f:
        for text in content:
            f.write(text + '\n\n')
    
    print(f"转换完成！已保存到: {txt_path}")

def main():
    """主函数"""
    # 检查Python版本
    if sys.version_info[0] < 3:
        raise Exception("必须使用Python 3")
    
    # 解析命令行参数
    args = parse_args()
    
    # 设置输出文件路径
    output_path = args.output if args.output else args.filename.rsplit('.', 1)[0] + '.txt'
    
    # 执行转换
    epub_to_txt(args.filename, output_path)

if __name__ == '__main__':
    main()