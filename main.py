#!/usr/bin/env python
# -*- coding: utf_8 -*- 

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

import argparse
from zipfile import ZipFile
import requests

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-c", "--columns", help="save text as parallel texts, with both languages side by side", action="store_true")
parser.add_argument("-s", "--sourcelang", dest="sourcelang", help="language of source epub file")
parser.add_argument("-t", "--targetlang", dest="targetlang", help="language to translate to")
parser.add_argument("-f", "--file", dest="filename", help="read epub from FILE", metavar="FILE")
parser.add_argument("-o", "--outfile", dest="out_filename", help="write translated epub to FILE", metavar="FILE")
parser.add_argument("-d", "--donotranslate", dest="donotranslate", help="test run, do not translate", action="store_true")
parser.add_argument("--model", default="llama2", dest="model", help="Ollama model name to use. Default is llama2")
parser.add_argument("--glossary", dest="glossary_file", help="TSV file containing translation glossary")

args = parser.parse_args()

sourcelang = "en"
targetlang = "es"
if args.sourcelang:
    sourcelang = args.sourcelang
if args.targetlang:
    targetlang = args.targetlang

filename = "test.epub"
out_filename = "out.epub"
if args.filename:
    filename = args.filename
if args.out_filename:
    out_filename = args.out_filename

OLLAMA_API = "http://localhost:11434/api/generate"
model = args.model

def is_printable(s):
    return not any(repr(ch).startswith("'\\x") or repr(ch).startswith("'\\u") for ch in s)

def translatable(string):
    if (not string):
        return False
    if (not is_printable(string)):
        return False
    if (string.isspace()):
        return False
    if (not string.strip()):
        return False
    if (string == '\n'):
        return False
    return True

def load_glossary(file_path):
    """加载TSV翻译对照表"""
    glossary = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                source, target = line.strip().split('\t')
                glossary.append((source.strip(), target.strip()))
        return glossary
    except Exception as e:
        print(f"加载翻译对��表失败: {e}")
        return []
    
def call_ollama(prompt, model="llama2"):
    """
    调用Ollama API进行文本生成
    
    参数:
        prompt: 输入提示文本
        model: 使用的模型名称，默认为"llama2"
        
    返回:
        生成的文本响应，如果调用失败则返回空字符串
    """
    if args.verbose:
        print("prompt:", prompt)
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    
    if response.status_code == 200:
        if args.verbose:
            print("response:", response.json()['response'])
        return response.json()['response'].strip()
    else:
        raise Exception(f"调用Ollama API失败: HTTP {response.status_code}")
            

def extract_translation_by_model(response, model="llama2"):
    """使用模型提取翻译结果的核心内容"""
    prompt = f"""请从以下文本中提取出实际的翻译结果，去除所有解释性文字、标注等内容。只需要返回翻译后的文本：

{response}

只返回最终的翻译结果："""
    
    clean_response = call_ollama(prompt, model)
    return clean_response.strip()

def extract_yes_no(response, model="llama2"):
    """从响应中提取"是"或"否"的明确答案"""
    prompt = f"""请从以下回答中仅提取出"是"或"否"的结论
```
{response}
```

请仅返回"是"或"否"
"""
    result = call_ollama(prompt, model).strip().lower()
    return result in ["是", "yes", "true", "对", "正确"]

def translate_with_context(text, context_before="", context_after="", sourcelang="en", targetlang="zh", model="llama2", tag="", glossary=[]):
    """带上下文的单句翻译"""
    if tag in ["title", "style"]:
        return text
        
    # 首先判断是否需要翻译
    check_prompt = f"""在将以下文本从{sourcelang}翻译成{targetlang}时，请判断以下文本是否需要翻译（是/否）。判断标准：
1. **专有名词**：如公司名称、品牌、产品名称等。它们在全球范围内通常保持不变。
2. **地名**：有些地名不需要翻译，如纽约（New York），保持原名更能被理解。
3. **技术术语**：一些技术术语可能在专业领域更容易用原文理解，如“AI”、“JavaScript”等。
4. **引用或商标**：如某些书籍、电影、歌曲的原文标题，或者带有商标符号的名称。
5. **文化独特词汇**：某些词汇在原语言中有特殊的文化含义或表达方式，翻译可能无法准确传达原意。

文本：`{text}`

请分析并做判断。"""

    initial_response = call_ollama(check_prompt, model)
    need_translation = extract_yes_no(initial_response, model)
    
    if not need_translation:
        if args.verbose:
            print(f"跳过翻译: {text}")
        return text
    
    # 构建词汇表提示
    glossary_prompt = ""
    if glossary:
        glossary_prompt = "请参考以下翻译对照表：\n"
        for source, target in glossary:
            glossary_prompt += f"{source} => {target}\n"
        glossary_prompt += "\n"
    
    prompt = f"""{glossary_prompt}请将以下文本从{sourcelang}翻译成{targetlang}。只需翻译 ### 之间的文本，上文仅供参考。
请翻译两遍，第一遍翻译时，请直译；第二遍翻译时，请综合考虑，如有必要，进行适当调整。

上文参考：
{context_before}

###
{text}
###

Translation:"""
    response = call_ollama(prompt, model)
    
    cleaned_translation = extract_translation_by_model(response, model)
    return cleaned_translation
    

def format_parallel_text(original, translated):
    """格式化双语对照文本"""
    return f"""<table style="width: 100%;"><tbody><tr>
        <td style="width: 50%; padding-right:6pt; vertical-align: top;">{original}</td>
        <td style="width: 50%; padding-left:6pt; vertical-align: top;">{translated}</td>
    </tr></tbody></table>"""

# 在主循环之前添加上下文管理
context_window = []
context_size = 2  # 保存前后各两句话作为上下文

def update_context(text):
    """更新上下文窗口"""
    if translatable(text):
        context_window.append(text)
        if len(context_window) > context_size * 2 + 1:
            context_window.pop(0)
            
def get_context(current_index):
    """获取当前文本的上下文"""
    if len(context_window) <= 1:
        return "", ""
        
    current_pos = context_window.index(context_window[current_index])
    
    # 获取前文
    before_text = " ".join(context_window[max(0, current_pos-context_size):current_pos])
    
    # 获取后文
    after_text = " ".join(context_window[current_pos+1:min(current_pos+1+context_size, len(context_window))])
    
    return before_text, after_text

# 在主循环中使用批量翻译
batch_size = 5  # 每批翻译的文本数量
texts_to_translate = []
tags_to_translate = []
translated_results = []

# 加载词汇表
glossary = []
if args.glossary_file:
    glossary = load_glossary(args.glossary_file)
    if args.verbose:
        print(f"已加载 {len(glossary)} 个翻译对照条目")

with ZipFile(filename, 'r') as zip:
    with ZipFile(out_filename, 'w') as zout:
        for info in zip.infolist():
            
            filedata = zip.read(info.filename)

            if (info.filename.endswith('html') or info.filename.endswith('ncx')):
                originaldata = str(filedata.decode())

                inside_tag = 0
                file_data = ""
                original_text = ""
                translated_text = ""
                tag = ""
                tagspace = False

                for char_index in range(len(originaldata)):
                    if (originaldata[char_index] == "<"):
                        inside_tag += 1
                        if (translatable(original_text)):
                            if args.verbose:
                                print("translatable:", original_text)
                            if translatable(original_text):
                                update_context(original_text)
                                context_before, context_after = get_context(-1)  # 获取最后一个文本的上下文
                                translated_text = translate_with_context(original_text, context_before, context_after, sourcelang, targetlang, model, tag)
                            
                            translated_text = translated_results.pop(0) if translated_results else original_text
                            
                            # 添加到输出
                            if args.columns:
                                if tag in ["title", "style"]:
                                    file_data += original_text
                                else:
                                    file_data += format_parallel_text(original_text, translated_text)
                            else:
                                file_data += translated_text
                        else:
                            file_data += original_text
                        original_text = ""
                        tag = ""
                        tagspace = False
                    elif (originaldata[char_index] == ">"):
                        inside_tag -= 1
                    elif inside_tag > 0:
                        file_data += originaldata[char_index]
                        if originaldata[char_index] == ' ':
                            tagspace = True
                        if not tagspace:
                            tag += originaldata[char_index]
                    else:
                        original_text += originaldata[char_index]

                zout.writestr(info.filename, file_data)
            else:
                zout.writestr(info.filename, filedata)

        print('Done!')
