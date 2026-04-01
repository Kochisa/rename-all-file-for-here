import os
import sys
import shutil
from pathlib import Path

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 >nul')
    # 设置 Python 使用 UTF-8 编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def process_files(base_dir, max_depth=10):
    """
    遍历 base_dir 下的所有文件夹，将文件按文件夹层级重命名并复制到 base_dir
    
    :param base_dir: 基础目录路径
    :param max_depth: 最大递归深度
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"错误：目录 {base_dir} 不存在")
        return
    
    print(f"开始处理目录：{base_dir}")
    print(f"最大递归深度：{max_depth}")
    print("-" * 60)
    
    processed_count = 0
    error_count = 0
    deleted_count = 0  # 删除的 Thumbs.db 数量
    error_files = []  # 收集出错的文件名
    
    # 遍历 base_dir 下的所有一级子目录
    for folder in base_path.iterdir():
        if not folder.is_dir():
            continue
            
        folder_name = folder.name
        print(f"\n处理文件夹：{folder_name[:100]}...")
        
        # 递归处理该文件夹下的所有文件
        processed_count, error_count, deleted_count, error_files = process_folder(folder, base_path, [folder_name], max_depth, processed_count, error_count, deleted_count, error_files)
    
    print("\n" + "=" * 60)
    print(f"处理完成！共处理 {processed_count} 个文件，删除 {deleted_count} 个系统文件，{error_count} 个错误")
    
    # 如果有错误，显示出错的文件名
    if error_files:
        print("\n以下文件处理出错：")
        for i, filename in enumerate(error_files, 1):
            print(f"  {i}. {filename}")

def truncate_name(name, max_length=255):
    """
    对文件名进行缩略处理
    文件夹部分保留前后 6 个字符
    原文件名字部分保留后 20 个字符（从后往前数），如果不够长则不缩略
    但保持日期格式（YYYY-MM-DD）不变
    """
    import re
    
    # 分割名称（按空格分割）
    parts = name.split(' ')
    
    if len(parts) <= 1:
        # 只有一个部分，直接处理（这是原文件名）
        if len(parts) == 1:
            part = parts[0]
            # 检查是否是日期格式
            if is_date_format(part):
                return part  # 日期格式不处理
            else:
                # 原文件名，保留后20个字符，如果不够长则不缩略
                if len(part) > 23:  # 20 + 3个省略号
                    return '...' + part[-20:]
                return part
        return name
    
    # 多个部分，需要区分文件夹部分和原文件名部分
    # 简单策略：假设只有第一个部分是文件夹名，其余都是原文件名
    folder_parts_count = 1  # 假设只有第一个部分是文件夹名
    
    # 处理文件夹部分（前缀）
    truncated_parts = []
    for i in range(folder_parts_count):
        part = parts[i]
        # 检查是否是日期格式
        if is_date_format(part):
            truncated_parts.append(part)  # 日期格式不处理
        else:
            # 文件夹名，保留前后6个字符
            if len(part) > 15:
                truncated = part[:6] + '...' + part[-6:]
            else:
                truncated = part
            truncated_parts.append(truncated)
    
    # 处理原文件名部分（剩余所有部分）
    filename_parts = parts[folder_parts_count:]
    filename = ' '.join(filename_parts)
    
    # 原文件名保留后20个字符，如果不够长则不缩略
    if len(filename) > 23:  # 20 + 3个省略号
        truncated_filename = '...' + filename[-20:]
    else:
        truncated_filename = filename
    
    truncated_parts.append(truncated_filename)
    
    result = ' '.join(truncated_parts)
    
    # 如果结果仍然超长，再次截断
    if len(result) > max_length:
        return result[:max_length-3] + '...'
    
    return result

def is_date_format(s):
    """
    检查字符串是否是日期格式（YYYY-MM-DD）
    """
    import re
    # 匹配 YYYY-MM-DD 格式
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, s))

def sanitize_filename(name):
    """
    清理文件名中的非法字符
    Windows 文件名不能包含：< > : " \ / | ? *
    将这些字符替换为下划线
    """
    # 定义非法字符
    illegal_chars = ['<', '>', ':', '"', '\\', '/', '|', '?', '*']
    
    # 替换非法字符
    sanitized = name
    for char in illegal_chars:
        sanitized = sanitized.replace(char, '_')
    
    # 移除控制字符 (ASCII 0-31)
    sanitized = ''.join(c for c in sanitized if ord(c) >= 32)
    
    return sanitized.strip()

def process_folder(current_path, base_path, name_parts, max_depth, count, error_count, deleted_count, error_files):
    """
    递归处理文件夹
    
    :param current_path: 当前文件夹路径
    :param base_path: 基础目录路径
    :param name_parts: 名称组成部分列表
    :param max_depth: 最大递归深度
    :param count: 已处理的文件计数
    :param error_count: 错误计数
    :param deleted_count: 删除的系统文件计数
    :param error_files: 出错的文件名列表
    """
    if len(name_parts) > max_depth:
        print(f"  跳过：超过最大深度 {max_depth}")
        return count, error_count, deleted_count, error_files
    
    # 生成文件名前缀
    prefix = " ".join(name_parts)
    
    # 处理当前文件夹中的所有文件（不包括子文件夹）
    for item in current_path.iterdir():
        if item.is_file():
            # 跳过并删除 Thumbs.db 文件
            if item.name.lower() == 'thumbs.db':
                try:
                    os.remove(str(item))
                    deleted_count += 1
                    print(f"  删除系统文件：{item.name}")
                except Exception as e:
                    print(f"  无法删除 {item.name}: {str(e)[:100]}")
                continue
            
            # 生成新文件名
            new_name = f"{prefix} {item.name}"
            # 清理非法字符
            new_name = sanitize_filename(new_name)
            # 检查是否需要缩略
            new_name = truncate_name(new_name)
            # 目标路径 - 直接使用字符串拼接
            dst = str(base_path) + '\\' + new_name
            
            # 检查目标文件是否已存在
            if os.path.exists(dst):
                print(f"  跳过 (已存在): {new_name[:150]}...")
                continue
            
            # 移动文件
            src = str(item)
            try:
                # 使用 copy2 + remove 而不是 move，避免 SMB 挂载问题
                shutil.copy2(src, dst)
                os.remove(src)
                count += 1
                print(f"  移动：{item.name[:100]}... -> {new_name[:150]}...")
            except FileExistsError:
                print(f"  跳过 (已存在): {new_name[:150]}...")
            except Exception as e:
                error_count += 1
                error_files.append(item.name)  # 记录出错的文件名
                print(f"  错误：{item.name[:100]}... - {str(e)[:100]}")
        
        elif item.is_dir() and len(name_parts) < max_depth:
            # 递归处理子文件夹
            new_name_parts = name_parts + [item.name]
            count, error_count, deleted_count, error_files = process_folder(item, base_path, new_name_parts, max_depth, count, error_count, deleted_count, error_files)
    
    return count, error_count, deleted_count, error_files

if __name__ == "__main__":
    # 使用当前工作目录
    cedar_dir = os.getcwd()
    max_depth = 10
    
    # 显示当前目录
    print("=" * 60)
    print("文件重命名复制工具")
    print("=" * 60)
    print(f"当前目录：{cedar_dir}")
    print(f"最大递归深度：{max_depth}")
    print("\n此工具将：")
    print("1. 遍历当前目录下所有一级子文件夹")
    print("2. 将每个文件按文件夹层级重命名")
    print("3. 移动到当前目录")
    print("\n例如：")
    print("  .\\2024-05-21\\post.json")
    print("  -> .\\2024-05-21 post.json")
    print("\n  .\\2024-05-21\\xxxx\\post.json")
    print("  -> .\\2024-05-21 xxxx post.json")
    print("=" * 60)
    
    try:
        process_files(cedar_dir, max_depth)
    except Exception as e:
        print(f"\n发生错误：{str(e)}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")
