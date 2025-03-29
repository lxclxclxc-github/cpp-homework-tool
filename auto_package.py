import os
import re
import shutil
import zipfile
import sys
import subprocess
import webbrowser

def get_student_id():
    """获取学生学号，从配置文件读取，否则询问用户并设置"""
    # 尝试从配置文件读取
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_config.txt")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                student_id = f.read().strip()
            if is_valid_student_id(student_id):
                print(f"从配置文件读取到学号: {format_student_id(student_id)}")
                confirm = input(f"确认你的学号是 {format_student_id(student_id)} 吗？(y/n): ")
                if confirm.lower() == 'y':
                    return student_id
        except Exception as e:
            print(f"读取配置文件出错: {e}")
    
    # 如果配置文件不存在或无效，询问用户输入
    return request_and_set_student_id()

def is_valid_student_id(student_id):
    """检查学号是否为12位数字"""
    return bool(re.match(r'^\d{12}$', student_id))

def format_student_id(student_id):
    """将学号格式化为4位4位4位的形式"""
    if len(student_id) == 12:
        return f"{student_id[0:4]} {student_id[4:8]} {student_id[8:12]}"
    return student_id

def request_and_set_student_id():
    """请求用户输入学号并进行验证、设置"""
    while True:
        student_id = input("请输入你的学号(12位数字): ")
        
        if not is_valid_student_id(student_id):
            print("错误: 学号必须是12位数字，请重新输入")
            continue
        
        # 格式化显示并确认
        formatted_id = format_student_id(student_id)
        confirm = input(f"确认你的学号是 {formatted_id} 吗？(y/n): ")
        if confirm.lower() == 'y':
            break
    
    # 保存到配置文件
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_config.txt")
    try:
        with open(config_file, "w") as f:
            f.write(student_id)
        print(f"已将学号保存到配置文件")
    except Exception as e:
        print(f"警告: 无法保存学号到配置文件: {e}")
    
    print(f"已设置学号: {formatted_id}")
    return student_id

def find_latest_assignment_folder(base_path):
    """查找具有最大编号的assignmentx文件夹"""
    assignment_pattern = re.compile(r'assignment(\d+)$')
    max_num = -1
    latest_folder = None
    
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            match = assignment_pattern.match(item)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
                    latest_folder = item_path
    
    if latest_folder:
        print(f"找到最新的作业文件夹: {latest_folder}")
        return latest_folder
    else:
        print("未找到任何assignment文件夹")
        return None

def is_valid_subfolder(folder_name):
    """检查文件夹名称是否符合x_yyy格式"""
    pattern = re.compile(r'^\d+_\w+$')
    return bool(pattern.match(folder_name))

def create_zip_package(assignment_folder, student_id):
    """创建打包文件，包含符合条件的子文件夹中的所有.cpp和.h文件"""
    if not os.path.exists(assignment_folder):
        print(f"找不到文件夹: {assignment_folder}")
        return False
    
    # 创建临时目录用于存放要打包的文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(current_dir, f"temp_package_{student_id}")
    
    # 如果临时目录已存在，先删除
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    os.makedirs(temp_dir)
    
    valid_subfolders = []
    total_files_copied = 0
    all_copied_files = []  # 用于存储所有复制的文件信息
    
    # 遍历assignment文件夹中的所有子文件夹
    for item in os.listdir(assignment_folder):
        subfolder_path = os.path.join(assignment_folder, item)
        if os.path.isdir(subfolder_path) and is_valid_subfolder(item):
            # 检查文件夹中是否有.cpp或.h文件
            cpp_h_files = []
            for file in os.listdir(subfolder_path):
                if file.endswith(".cpp") or file.endswith(".h"):
                    cpp_h_files.append(file)
            
            if cpp_h_files:
                # 在临时目录中创建对应的子文件夹
                temp_subfolder = os.path.join(temp_dir, item)
                os.makedirs(temp_subfolder)
                
                # 记录当前文件夹的复制情况
                folder_files = []
                
                # 复制所有.cpp和.h文件到临时目录对应的子文件夹中
                for file in cpp_h_files:
                    src_file = os.path.join(subfolder_path, file)
                    shutil.copy2(src_file, temp_subfolder)
                    total_files_copied += 1
                    folder_files.append(file)
                
                valid_subfolders.append(item)
                all_copied_files.append((item, folder_files))
    
    if not valid_subfolders:
        print("没有找到符合条件的子文件夹或.cpp/.h文件")
        shutil.rmtree(temp_dir)
        return False
    
    # 打印复制的文件详情
    print("\n文件复制详情:")
    for folder, files in all_copied_files:
        print(f"文件夹 {folder} 中复制了以下文件:")
        for f in files:
            print(f"  - {f}")
    
    # 创建zip文件（放在assignment文件夹内）
    zip_filename = os.path.join(assignment_folder, f"{student_id}.zip")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算相对路径，以便在zip中保持文件夹结构
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # 清理临时目录
    shutil.rmtree(temp_dir)
    
    print(f"\n包含以下子文件夹: {', '.join(valid_subfolders)}")
    print(f"总共打包了 {total_files_copied} 个文件")
    return zip_filename

def main():
    print("一键打包程序 - 打包所有.cpp和.h文件")
    
    # 获取学生学号
    student_id = get_student_id()
    
    # 获取当前脚本所在的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找最新的assignment文件夹
    latest_assignment = find_latest_assignment_folder(current_dir)
    
    if not latest_assignment:
        print("错误: 未找到任何assignment文件夹，请确保脚本与作业文件夹在同一目录")
        input("按任意键退出...")
        return
    
    # 创建打包文件
    zip_path = create_zip_package(latest_assignment, student_id)
    print("\n")
    if zip_path:
        print(f"打包成功! 文件已保存为: {latest_assignment}\\{student_id}.zip")
        
        # 询问是否打开交作业网站
        open_website = input("是否打开交作业网站？(y/n): ")
        if open_website.lower() == 'y':
            webbrowser.open("https://oc.sjtu.edu.cn/courses/75883/assignments")
            print("已打开交作业网站")
    else:
        print("打包失败!")
    
    input("按任意键退出...")

if __name__ == "__main__":
    main()