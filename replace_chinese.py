#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
替换tex文件中的汉字为随机汉字
排除指定字符
不替换%注释符号后面的内容
脚注命令中的脚注名称替换为唯一数字ID
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
    不替换特定命令的第一个方括号中的内容（这些内容会被替换为唯一数字ID）
    """
    # 维护字符串到ID的映射（相同字符串使用相同ID）
    string_to_id = {}
    next_id = 1

    def get_string_id(protected_string):
        """获取字符串对应的ID，如果不存在则分配新ID"""
        nonlocal next_id
        if protected_string not in string_to_id:
            string_to_id[protected_string] = next_id
            next_id += 1
        return string_to_id[protected_string]
    def replace_char(match):
        char = match.group(0)
        # 如果字符在排除列表中，不替换
        if char in EXCLUDED_CHARS:
            return char
        # 否则替换为随机汉字
        return random.choice(CHINESE_CHARS)

    # 匹配所有汉字（Unicode范围 \u4e00-\u9fff）
    pattern = r'[\u4e00-\u9fff]'

    # 需要保护第一个方括号的命令列表（直接使用正则表达式模式）
    # 在正则表达式中，\\匹配字面的反斜杠
    # 在Python原始字符串中，r'\\'表示一个字面的反斜杠
    # 所以r'\\startbuffer'在正则中就是\\startbuffer，会匹配字面的\startbuffer
    protected_commands = [
        r'\\startbuffer',      # 正则模式：匹配 \startbuffer
        r'\\firstfootnote',    # 正则模式：匹配 \firstfootnote
        r'\\tofirstfootnote',  # 正则模式：匹配 \tofirstfootnote
        r'\\sameasfootnote',   # 正则模式：匹配 \sameasfootnote
        r'\\basefootnote'      # 正则模式：匹配 \basefootnote
    ]

    # 按行处理，保留%注释后的内容
    lines = text.split('\n')
    processed_lines = []

    for line in lines:
        # 查找%的位置（需要考虑转义的\%）
        comment_pos = -1
        for i, char in enumerate(line):
            if char == '%' and (i == 0 or line[i-1] != '\\'):
                comment_pos = i
                break

        # 确定需要处理的部分（%之前的内容）
        if comment_pos >= 0:
            text_to_process = line[:comment_pos]
            comment_part = line[comment_pos:]
        else:
            text_to_process = line
            comment_part = ''

        # 保护特定命令的方括号内容
        # 使用占位符标记受保护的区域
        protected_regions = []
        # 使用特殊Unicode字符作为占位符前缀，确保不会与文本内容冲突
        placeholder_template = '\uE000PROTECTED{}\uE001'
        placeholder_counter = 0

        for cmd_pattern_base in protected_commands:
            # 对于\firstfootnote，需要特殊处理：可能保护1个或2个方括号
            if cmd_pattern_base == r'\\firstfootnote':
                # 匹配\firstfootnote[xxx][xxx][...]形式（保护前两个方括号）
                pattern_two = cmd_pattern_base + r'\[([^\]]+)\]\[([^\]]+)\]'
                matches_two = list(re.finditer(pattern_two, text_to_process))

                # 匹配\firstfootnote[xxx][...]形式（只保护第一个方括号）
                pattern_one = cmd_pattern_base + r'\[([^\]]+)\]'
                matches_one = list(re.finditer(pattern_one, text_to_process))

                # 处理两个方括号的情况（从后往前处理，避免位置偏移）
                for match in reversed(matches_two):
                    # 获取两个方括号中的内容
                    bracket1_content = match.group(1)  # 第一个方括号
                    bracket2_content = match.group(2)  # 第二个方括号
                    bracket1_start = match.start(1)
                    bracket1_end = match.end(1)
                    bracket2_start = match.start(2)
                    bracket2_end = match.end(2)

                    # 获取字符串对应的ID
                    id1 = get_string_id(bracket1_content)
                    id2 = get_string_id(bracket2_content)

                    # 创建占位符
                    placeholder1 = placeholder_template.format(placeholder_counter)
                    placeholder_counter += 1
                    placeholder2 = placeholder_template.format(placeholder_counter)
                    placeholder_counter += 1

                    # 记录占位符和对应的ID（而不是原始内容）
                    protected_regions.append((placeholder1, str(id1)))
                    protected_regions.append((placeholder2, str(id2)))

                    # 从后往前替换：先替换第二个方括号，再替换第一个
                    # 因为第二个在第一个之后，替换第二个不会影响第一个的位置
                    text_to_process = (text_to_process[:bracket2_start] +
                                      placeholder2 +
                                      text_to_process[bracket2_end:])
                    # 第一个方括号的位置不变（因为第二个在它后面，替换第二个不影响第一个）
                    text_to_process = (text_to_process[:bracket1_start] +
                                      placeholder1 +
                                      text_to_process[bracket1_end:])

                # 记录已处理的匹配位置，避免重复处理
                processed_positions = {match_two.start(0) for match_two in matches_two}

                # 处理只有一个方括号的情况（排除已经被两个方括号匹配的情况）
                for match in reversed(matches_one):
                    # 检查这个匹配是否已经被两个方括号的情况处理过
                    if match.start(0) not in processed_positions:
                        # 获取第一个方括号中的内容
                        bracket_content = match.group(1)
                        bracket_start = match.start(1)
                        bracket_end = match.end(1)

                        # 获取字符串对应的ID
                        string_id = get_string_id(bracket_content)

                        # 创建占位符
                        placeholder = placeholder_template.format(placeholder_counter)
                        placeholder_counter += 1

                        # 记录占位符和对应的ID（而不是原始内容）
                        protected_regions.append((placeholder, str(string_id)))

                        # 替换方括号中的内容为占位符
                        text_to_process = (text_to_process[:bracket_start] +
                                          placeholder +
                                          text_to_process[bracket_end:])
            else:
                # 其他命令：只保护第一个方括号
                cmd_pattern = cmd_pattern_base + r'\[([^\]]+)\]'
                matches = list(re.finditer(cmd_pattern, text_to_process))

                for match in reversed(matches):  # 从后往前处理，避免位置偏移
                    # 获取第一个方括号中的内容
                    bracket_content = match.group(1)  # 例如：xxx
                    bracket_start = match.start(1)  # 方括号内容的起始位置
                    bracket_end = match.end(1)  # 方括号内容的结束位置

                    # 获取字符串对应的ID
                    string_id = get_string_id(bracket_content)

                    # 创建占位符
                    placeholder = placeholder_template.format(placeholder_counter)
                    placeholder_counter += 1

                    # 记录占位符和对应的ID（而不是原始内容）
                    protected_regions.append((placeholder, str(string_id)))

                    # 只替换方括号中的内容为占位符
                    text_to_process = (text_to_process[:bracket_start] +
                                      placeholder +
                                      text_to_process[bracket_end:])

        # 对处理后的文本进行汉字替换
        processed_text = re.sub(pattern, replace_char, text_to_process)

        # 恢复受保护的区域（按相反顺序恢复，使用精确替换）
        for placeholder, original in reversed(protected_regions):
            # 使用精确替换，确保只替换占位符
            processed_text = processed_text.replace(placeholder, original, 1)

        # 组合结果
        processed_lines.append(processed_text + comment_part)

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

