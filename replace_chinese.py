#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
替换tex文件中的汉字为随机汉字
排除字符：序跋目录第章一二三四五六七八九十廿卅
"""

import re
import random
from pathlib import Path


# 排除的汉字列表
EXCLUDED_CHARS = set('序跋目录第章一二三四五六七八九十廿卅版权页占位')

# 生成简体字字符列表（使用GB2312字符集）
def get_chinese_chars():
    """生成所有可用的简体字字符列表（基于GB2312字符集）"""
    chars = []
    # 使用GB2312编码来验证简体字
    # GB2312编码范围：0xA1A1-0xFEFE
    for row in range(0xA1, 0xFE + 1):
        for col in range(0xA1, 0xFE + 1):
            try:
                # 尝试将GB2312字节编码为字符
                byte_pair = bytes([row, col])
                char = byte_pair.decode('gb2312')
                # 检查是否为汉字（排除标点符号等）
                if '\u4e00' <= char <= '\u9fff' and char not in EXCLUDED_CHARS:
                    chars.append(char)
            except (UnicodeDecodeError, ValueError, LookupError):
                # 跳过无效的GB2312编码或编码不支持的情况
                continue
    return chars


# 预生成汉字列表
CHINESE_CHARS = get_chinese_chars()


def replace_chinese_in_text(text):
    """
    替换文本中的汉字为随机汉字
    不替换排除列表中的字符和其他非汉字字符
    不替换%注释符号后面的内容
    """
    def replace_char(match):
        char = match.group(0)
        # 如果字符在排除列表中，不替换
        if char in EXCLUDED_CHARS:
            return char
        # 否则替换为随机汉字
        return random.choice(CHINESE_CHARS)
    
    # 匹配所有汉字（Unicode范围 \u4e00-\u9fff）
    pattern = r'[\u4e00-\u9fff]'
    
    # 按行处理，保留%注释后的内容
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        # 查找%的位置（需要考虑转义的\%）
        # 使用负向前瞻，确保%前面不是反斜杠
        comment_pos = -1
        for i, char in enumerate(line):
            if char == '%' and (i == 0 or line[i-1] != '\\'):
                comment_pos = i
                break
        
        if comment_pos >= 0:
            # 有注释：只替换%之前的部分
            before_comment = line[:comment_pos]
            after_comment = line[comment_pos:]
            replaced_part = re.sub(pattern, replace_char, before_comment)
            processed_lines.append(replaced_part + after_comment)
        else:
            # 无注释：整行都处理
            processed_lines.append(re.sub(pattern, replace_char, line))
    
    return '\n'.join(processed_lines)


def process_tex_file(file_path):
    """
    处理单个tex文件
    """
    try:
        # 读取文件（使用utf-8编码）
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换汉字
        new_content = replace_chinese_in_text(content)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"已处理: {file_path}")
        return True
    except Exception as e:
        print(f"处理 {file_path} 时出错: {e}")
        return False


def main():
    """
    主函数：查找并处理根目录中的tex文件（不处理子文件夹）
    """
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    
    # 只查找根目录中的.tex文件（不递归子文件夹）
    tex_files = list(script_dir.glob('*.tex'))
    
    if not tex_files:
        print("未找到任何.tex文件")
        return
    
    print(f"找到 {len(tex_files)} 个.tex文件")
    print("开始处理...")
    print("-" * 50)
    
    # 处理每个文件
    success_count = 0
    for tex_file in tex_files:
        if process_tex_file(tex_file):
            success_count += 1
    
    print("-" * 50)
    print(f"处理完成！成功处理 {success_count}/{len(tex_files)} 个文件")


if __name__ == '__main__':
    main()

