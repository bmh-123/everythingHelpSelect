import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List

def get_everything_results(keyword: str) -> List[Dict]:
    """调用Everything命令行工具es.exe获取搜索结果 """
    try:
        cmd = f'es.exe -s -n 100 -sort dm "{keyword}"'
        result = subprocess.check_output(cmd, encoding='utf-8', shell=True)
        files = [line.strip() for line in result.split('\n') if line.strip()]
        
        file_infos = []
        for file_path in files:
            if not os.path.exists(file_path):
                continue
            
            stat = os.stat(file_path)
            modify_time = datetime.fromtimestamp(stat.st_mtime)
            file_name = os.path.basename(file_path)
            
            file_infos.append({
                "path": file_path,
                "name": file_name,
                "modify_time": modify_time,
                "modify_timestamp": stat.st_mtime
            })
        return file_infos
    except Exception as e:
        print(f"调用Everything失败：{e}")
        return []

def extract_file_series_enhanced(file_name: str) -> str:
    """增强版文件系列名提取函数 - 覆盖所有常见迭代后缀"""
    base_name = os.path.splitext(file_name)[0]
    
    # 核心增强正则表达式
    pattern = r'''
        (
            -[\s]*副本|_副本|\(副本\)|（副本）|
            \(\d+\)|（\d+）|
            _v?er?\d+|_-?v?er?\d+|
            -v?er?\d+|
            _\d+|-\d+|\d+$|
            _?v\d+|_?V\d+|
            # _\d{8}|-\d{8}  # 如需排除8位日期后缀请取消注释
        )$
    '''
    
    series_name = re.sub(
        pattern, 
        '', 
        base_name, 
        flags=re.VERBOSE | re.IGNORECASE
    )
    
    series_name = series_name.rstrip('_- ')
    return series_name if series_name.strip() else base_name

def filter_latest_versions(file_infos: List[Dict]) -> List[Dict]:
    """筛选每个文件系列的最新版本"""
    series_groups = {}
    for file in file_infos:
        series = extract_file_series_enhanced(file["name"])
        if series not in series_groups:
            series_groups[series] = []
        series_groups[series].append(file)
    
    latest_files = []
    for series, files in series_groups.items():
        sorted_files = sorted(files, key=lambda x: x["modify_timestamp"], reverse=True)
        latest_files.append(sorted_files[0])
    
    latest_files.sort(key=lambda x: x["modify_timestamp"], reverse=True)
    return latest_files

def main():
    """主函数：输入关键词 → 调用Everything → 筛选最新版本 → 展示结果"""
    print("===== Everything + 智能最新版本筛选工具（增强版） =====")
    print("🔍 支持识别所有常见迭代后缀：-副本、(1)、_v2、-3、Ver5等\n")
    
    while True:
        keyword = input("请输入搜索关键词（输入q退出）：").strip()
        if keyword.lower() == 'q':
            print("程序退出...")
            break
        if not keyword:
            print("⚠️ 关键词不能为空！")
            continue
        
        print(f"\n正在使用Everything搜索 '{keyword}'...")
        file_infos = get_everything_results(keyword)
        if not file_infos:
            print("❌ 未找到匹配文件！")
            continue
        
        latest_files = filter_latest_versions(file_infos)
        
        print(f"✅ 共找到 {len(file_infos)} 个匹配文件，筛选出 {len(latest_files)} 个最新版本：")
        print("-" * 120)
        for i, file in enumerate(latest_files, 1):
            modify_time = file["modify_time"].strftime("%Y-%m-%d %H:%M:%S")
            series = extract_file_series_enhanced(file["name"])
            print(f"{i}. 【{modify_time}】【系列：{series}】 {file['name']}")
            print(f"    路径：{file['path']}")
        print("-" * 120)

if __name__ == "__main__":
    main()