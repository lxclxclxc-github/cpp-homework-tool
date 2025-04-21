import sys
import os
import re
import subprocess
import traceback
import tempfile
import shutil
import zipfile
from PyQt5 import sip
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextBrowser, QTreeWidget, QTreeWidgetItem, 
                            QDialog, QTabWidget, QMessageBox, QTextEdit, QScrollArea, 
                            QLineEdit, QDialogButtonBox, QSpacerItem, QSizePolicy,
                            QStyleFactory, QFrame, QCheckBox, QToolButton)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.setWindowIcon(QIcon("icon.ico"))  # 使用.ico文件

# 添加调试信息
print(f"程序启动时的当前目录: {os.getcwd()}")
print(f"可执行文件路径: {sys.executable if getattr(sys, 'frozen', False) else __file__}")

# 强制切换到当前脚本（或 EXE）的目录
if getattr(sys, 'frozen', False):  # 如果是 EXE 运行
    os.chdir(os.path.dirname(sys.executable))  # EXE 所在目录
else:  # Python 运行时
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # .py 所在目录
print(f"切换后的当前工作目录：{os.getcwd()}")
print(f"当前目录内容：{os.listdir()}")

# 定义无窗口子进程运行函数
def run_subprocess_no_window(cmd, **kwargs):
    """运行子进程但不显示命令行窗口"""
    # 仅在Windows上设置创建标志
    creation_flags = 0
    startupinfo = None
    
    if sys.platform.startswith('win'):
        # 设置CREATE_NO_WINDOW标志，防止显示控制台窗口
        creation_flags = subprocess.CREATE_NO_WINDOW
        
        # 也设置startupinfo，以防创建标志不起作用
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
    
    # 合并其他参数
    kwargs.update({
        'creationflags': creation_flags,
        'startupinfo': startupinfo
    })
    
    return subprocess.run(cmd, **kwargs)

def get_latest_assignment_folder():
    # 获取当前目录下所有文件夹，筛选出以 "assignment" 开头的文件夹
    folders = [f for f in os.listdir() if os.path.isdir(f) and f.startswith('assignment')]
    
    # 筛选出以 "challenge" 开头的文件夹
    if not folders:
        folders = [f for f in os.listdir() if os.path.isdir(f) and f.startswith('challenge')]

    # 如果没有找到符合的文件夹，返回 None
    if not folders:
        return None
    
    # 从符合的文件夹中提取出数字后缀并找出最大值
    max_number = -1
    latest_folder = None
    for folder in folders:
        match = re.search(r'(\d+)', folder)
        if match:
            number = int(match.group(1))
            if number > max_number:
                max_number = number
                latest_folder = folder
    
    return latest_folder

def get_folders_by_pattern():
    # 获取所有以 "x_yyy" 格式命名的文件夹
    pattern = r'^\d+_\w+$'
    folders = [f for f in os.listdir() if os.path.isdir(f) and re.match(pattern, f)]
    
    return folders

def run_test_case(task_folder, test_case_num, assignment_path):
    """运行单个测试案例并返回详细结果"""
    # 确保使用绝对路径
    assignment_path = os.path.abspath(assignment_path)
    
    # 导入judger_batch模块
    try:
        # 将作业目录添加到Python路径
        if assignment_path not in sys.path:
            sys.path.insert(0, assignment_path)
        
        # 尝试导入judger_batch模块
        try:
            from judger_batch import input_name, output_name, exec_name, get_random_filename
        except ImportError as e:
            # 如果导入失败，尝试在上级目录查找
            parent_dir = os.path.dirname(assignment_path)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from judger_batch import input_name, output_name, exec_name, get_random_filename
    except ImportError as e:
        return False, "导入错误", f"无法导入judger_batch模块: {str(e)}", None, None, None
    
    # 创建临时工作目录
    workdir = tempfile.mkdtemp()
    
    try:
        # 准备文件路径
        input_dir = os.path.join(assignment_path, 'data', task_folder)
        standard_dir = os.path.join(assignment_path, 'data', task_folder)
        source_dir = os.path.join(assignment_path, task_folder)
        
        # 检查必要的目录和文件是否存在
        if not os.path.exists(input_dir):
            return False, "输入目录不存在", f"找不到输入目录: {input_dir}", None, None, None
        if not os.path.exists(standard_dir):
            return False, "标准输出目录不存在", f"找不到标准输出目录: {standard_dir}", None, None, None
        if not os.path.exists(source_dir):
            return False, "源代码目录不存在", f"找不到源代码目录: {source_dir}", None, None, None
        
        main_dir = os.path.join(source_dir, exec_name[task_folder][0])
        exec_dir = os.path.join(workdir, exec_name[task_folder][1])
        
        # 检查源文件是否存在
        if not os.path.exists(main_dir):
            return False, "源文件不存在", f"找不到源文件: {main_dir}", None, None, None
        
        # 编译代码
        compile_cmd = ['g++', main_dir, '-o', exec_dir, '-g', '-Wall', '--std=c++11']
        cp_pro = run_subprocess_no_window(compile_cmd, capture_output=True)
        
        if cp_pro.returncode != 0:
            return False, "编译错误", cp_pro.stderr.decode('utf-8', errors='ignore'), None, None, None
        
        # 运行测试案例
        input_file = os.path.join(input_dir, input_name[test_case_num-1])
        standard_file = os.path.join(standard_dir, output_name[test_case_num-1])
        
        if not os.path.exists(input_file):
            return False, "输入文件不存在", f"找不到文件: {input_file}", None, None, None
        if not os.path.exists(standard_file):
            return False, "标准输出文件不存在", f"找不到文件: {standard_file}", None, None, None
        
        # 读取标准输入
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            input_content = f.read().strip()
        
        # 创建用户输出文件
        user_output_file = os.path.join(workdir, get_random_filename() + '.out')
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as fin, \
             open(user_output_file, 'w', encoding='utf-8', errors='ignore') as fout:
            try:
                run_subprocess_no_window(
                    [exec_dir], check=True, timeout=2,
                    stdin=fin, stdout=fout
                )
            except subprocess.TimeoutExpired:
                return False, "超时", "程序运行超时", input_content, None, None
            except subprocess.CalledProcessError as e:
                return False, "运行时错误", f"返回值: {e.returncode}", input_content, None, None
        
        # 读取用户输出和标准输出
        with open(user_output_file, 'r', encoding='utf-8', errors='ignore') as f:
            user_output_content = f.read().strip()
        with open(standard_file, 'r', encoding='utf-8', errors='ignore') as f:
            standard_output_content = f.read().strip()
        
        # 比较输出
        user_lines = user_output_content.split('\n')
        std_lines = standard_output_content.split('\n')
        
        if user_output_content == standard_output_content:
            return True, "正确", None, input_content, user_output_content, standard_output_content
        else:
            if len(user_lines) != len(std_lines):
                diff_msg = f"输出行数不同: 你的输出有 {len(user_lines)} 行，标准输出有 {len(std_lines)} 行"
            else:
                diff_lines = []
                for i, (user_line, std_line) in enumerate(zip(user_lines, std_lines)):
                    if user_line.rstrip() != std_line.rstrip():
                        diff_lines.append(i+1)
                diff_msg = "在第 " + ", ".join(str(i) for i in diff_lines) + " 行有差异"
            
            return False, "输出不匹配", diff_msg, input_content, user_output_content, standard_output_content
    
    finally:
        # 清理临时目录
        shutil.rmtree(workdir, ignore_errors=True)
        # 移除添加的路径
        if assignment_path in sys.path:
            sys.path.remove(assignment_path)
        if 'parent_dir' in locals() and parent_dir in sys.path:
            sys.path.remove(parent_dir)

def display_test_case_details(success, msg, details, input_content, user_output, std_output):
    """显示测试案例的详细信息，返回格式化后的字符串而不是直接打印"""
    output_lines = []
    
    if not success:
        output_lines.append(f"错误类型: {msg}")
        if details:
            output_lines.append(f"详细信息: {details}")
        
        # 添加标准输入
        if input_content:
            output_lines.append("\nStandard Input")
            output_lines.append("-" * 60)  # 使用更长的分隔线
            output_lines.append(input_content)
            output_lines.append("-" * 60)  # 使用更长的分隔线
        
        # 添加用户输出和标准输出
        if user_output is not None and std_output is not None:
            # 将输出分行以便对齐显示
            user_lines = user_output.split('\n')
            std_lines = std_output.split('\n')
            
            # 计算最大行数
            max_lines = max(len(user_lines), len(std_lines))
            
            output_lines.append(f"{'Your Output':<29} | {'Standard Output':<30}")
            output_lines.append("-" * 60)  # 使用更长的分隔线，确保覆盖两列
            
            # 对齐打印每一行
            for i in range(max_lines):
                user_line = user_lines[i] if i < len(user_lines) else ""
                std_line = std_lines[i] if i < len(std_lines) else ""
                output_lines.append(f"{user_line:<29} | {std_line:<30}")
            
            output_lines.append("-" * 60)  # 使用更长的分隔线
    else:
        output_lines.append("测试通过！")
        
        # 添加标准输入
        if input_content:
            output_lines.append("\n标准输入:")
            output_lines.append("-" * 60)  # 使用更长的分隔线
            output_lines.append(input_content)
            output_lines.append("-" * 60)  # 使用更长的分隔线
        
        # 添加用户输出（正确情况下与标准输出相同）
        if user_output is not None:
            output_lines.append("\n输出:")
            output_lines.append("-" * 60)  # 使用更长的分隔线
            output_lines.append(user_output)
            output_lines.append("-" * 60)  # 使用更长的分隔线
    
    # 返回格式化的字符串
    return "\n".join(output_lines)

def check_all_assignments(folders, assignment_path):
    all_passed = True
    for folder in sorted(folders):  # 确保按序号顺序检查
        x_value = folder.split('_')[0]
        print(f"\n正在检查第 {x_value} 题...")

        judger_path = os.path.join(assignment_path, "judger_batch.py")
        result = run_subprocess_no_window(["python", judger_path, "-T", folder],
                              capture_output=True, text=True)
        
        # 检查该题的所有测试点
        scores = re.findall(r'\[SCORE\] (\d+)', result.stdout)
        if scores and all(int(score) == 10 for score in scores):
            print(f"第 {x_value} 题通过啦"+int(x_value)*"✌️")
        else:
            print(f"第 {x_value} 题还需要改进 😢")
            print(result.stdout)
            
            # 找出失败的测试点
            test_points = re.findall(r'\[TEST POINT (\d+)\].*?\[SCORE\] (\d+)', result.stdout, re.DOTALL)
            for test_point, score in test_points:
                if int(score) != 10:
                    print(f"\n测试点 {test_point} 失败，正在获取详细信息...")
                    result = run_test_case(folder, int(test_point), assignment_path)
                    # 获取测试点详情并打印
                    details = display_test_case_details(*result)
                    print(details)
            
            all_passed = False
        print("="*50)
    if all_passed:
        print("\n🎉 太好啦，可以交作业啦！🎉")
    else:
        print("\n继续加油，马上就能完成啦！💪")
    
    return all_passed

def get_all_assignment_folders():
    """获取所有作业文件夹（包括assignment和challenge）"""
    # 添加调试信息
    current_dir = os.getcwd()
    print(f"get_all_assignment_folders函数中的当前目录: {current_dir}")
    print(f"目录内容: {os.listdir(current_dir)}")
    
    try:
        # 获取当前目录下所有文件夹，筛选出以 "assignment" 开头的文件夹
        assignment_folders = [f for f in os.listdir() if os.path.isdir(f) and f.startswith('assignment')]
        print(f"找到以assignment开头的文件夹: {assignment_folders}")
        
        # 筛选出以 "challenge" 开头的文件夹
        challenge_folders = [f for f in os.listdir() if os.path.isdir(f) and f.startswith('challenge')]
        print(f"找到以challenge开头的文件夹: {challenge_folders}")
        
        # 合并两种文件夹
        all_folders = assignment_folders + challenge_folders
        
        # 排序以便于显示，先按类型，再按数字
        def sort_key(folder):
            # 提取数字部分
            match = re.search(r'(\d+)', folder)
            if match:
                number = int(match.group(1))
            else:
                number = 0
            
            # assignment优先，然后按数字排序
            if folder.startswith('assignment'):
                return (0, number)
            else:
                return (1, number)
        
        all_folders.sort(key=sort_key)
        print(f"最终排序后的文件夹列表: {all_folders}")
        
        return all_folders
    except Exception as e:
        print(f"获取作业文件夹时出错: {str(e)}")
        traceback.print_exc()
        return []

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
                # 在GUI模式下，直接返回学号，不要求确认
                if 'PyQt5' in sys.modules:
                    return student_id
                    
                # 命令行模式下要求确认
                confirm = input(f"确认你的学号是 {format_student_id(student_id)} 吗？(y/n): ")
                if confirm.lower() == 'y':
                    return student_id
        except Exception as e:
            print(f"读取配置文件出错: {e}")
    
    # 如果配置文件不存在或无效，询问用户输入
    # 在GUI模式下，返回None让调用者处理
    if 'PyQt5' in sys.modules:
        return None
        
    # 命令行模式调用输入函数
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
    # 当作为GUI模块调用时直接返回空
    # 这可以防止终端输入引起的阻塞和循环
    if 'PyQt5' in sys.modules:
        print("在GUI模式下运行，跳过终端输入")
        return None
        
    # 下面的代码只在命令行模式下执行
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        student_id = input("请输入你的学号(12位数字): ")
        
        if not is_valid_student_id(student_id):
            print("错误: 学号必须是12位数字，请重新输入")
            continue
        
        # 格式化显示并确认
        formatted_id = format_student_id(student_id)
        confirm = input(f"确认你的学号是 {formatted_id} 吗？(y/n): ")
        if confirm.lower() == 'y':
            break
        
        if attempt == max_attempts:
            print("已达到最大尝试次数，退出")
            return None
    
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


# 定义全局样式
DARK_MODE = True  # 默认使用暗色模式

# 定义颜色方案
class Colors:
    # 暗色主题 - 更优雅的深色配色
    DARK = {
        'bg_primary': '#1a1d23',       # 主背景色 - 稍微更深一点
        'bg_secondary': '#242932',     # 次级背景 - 明暗区分更强
        'bg_tertiary': '#2e333d',      # 三层背景 - 用于卡片、面板底色

        'text_primary': '#e6eaf1',     # 主文本 - 更明亮，更易读
        'text_secondary': '#a1a8b5',   # 次文本 - 稍提亮，更通透
        
        'accent': '#4fc3f7',           # 主强调色 - 更亮的蓝色（带点霓虹感）
        'accent_alt': '#d57bee',       # 第二强调色 - 更偏紫粉，更醒目

        'success': '#89d185',          # 成功提示 - 稍鲜亮
        'warning': '#efc27b',          # 警告提示 - 提亮对比度
        'error': '#ef6b73',            # 错误提示 - 更鲜明红

        'border': '#1c1f26',           # 边框色 - 提高与背景的区分度
        'highlight': '#454b57',        # 高亮色 - 用于鼠标悬停等

        'link': '#5fdde5',             # 链接颜色 - 更加活泼灵动
        'test_pass': '#89d185',        # 测试通过 - 同 success
        'test_fail': '#ef6b73',        # 测试失败 - 同 error

        'scrollbar': '#444b58',        # 滚动条 - 略提亮，更清晰
        'checkbox': '#2e333d',         # 复选框 - 

        'title_1': '#7bc6ff',  # 稍冷、偏霓虹蓝
        'title_2': '#c1e192',  # 带点苹果绿 + 青柠感
        'title_3': '#c89cf0',  # 粉紫中加入一点蓝调，更清爽

        'package_button': '#ffffff'

    }

    
    # 浅色主题 - 更柔和的浅色配色
    LIGHT = {
        'bg_primary': '#fafafa',
        'bg_secondary': '#f0f0f0',
        'bg_tertiary': '#e5e5e5',
        'text_primary': '#383a42',
        'text_secondary': '#696c77',
        'accent': '#4078f2',
        'accent_alt': '#a626a4',  # 添加第二强调色
        'success': '#50a14f',
        'warning': '#c18401',
        'error': '#e45649',
        'border': '#d0d0d0',
        'highlight': '#e6e6e6',
        'link': '#0184bc',
        'test_pass': '#50a14f',
        'test_fail': '#e45649',
        'scrollbar': '#c1c1c1',
        'checkbox': '#26a69a',  # 复选框颜色
        'title_1': '#4ba0ff',   # 清新的淡蓝色，亮度提高，适合主标题
        'title_2': '#a2d77d',   # 明亮的草绿色，温暖且有层次感
        'title_3': '#d3a8f9',   # 淡紫色调，柔和但富有活力
        'package_button': '#333333'
    }
    
    @classmethod
    def current(cls):
        return cls.DARK if DARK_MODE else cls.LIGHT

# 设置应用字体
def set_app_fonts(app):
    # 添加中文字体支持，优先级从高到低
    chinese_fonts = ["微软雅黑", "Microsoft YaHei", "Source Han Sans CN", "思源黑体", "NotoSansCJK", "WenQuanYi Micro Hei", "文泉驿微米黑", "SimHei", "黑体"]
    
    # 现代等宽字体
    modern_fonts = ["JetBrains Mono", "Cascadia Code", "Fira Code", "Consolas", "Courier New"]
    
    # 尝试设置中文字体
    chosen_chinese_font = None
    for font_name in chinese_fonts:
        font = QFont(font_name, 10)
        if font.exactMatch():
            chosen_chinese_font = font_name
            break
    
    # 尝试设置现代等宽字体
    chosen_mono_font = None
    for font_name in modern_fonts:
        font = QFont(font_name, 10)
        if font.exactMatch():
            chosen_mono_font = font_name
            break
    
    # 如果找不到中文字体，设置默认中文字体
    if not chosen_chinese_font:
        chosen_chinese_font = "Sans-serif"
        
    # 如果找不到等宽字体，设置默认等宽字体
    if not chosen_mono_font:
        chosen_mono_font = "Monospace"
    
    # 设置应用的默认字体为中文字体
    font = QFont(chosen_chinese_font, 10)
    app.setFont(font)
    
    return {"chinese": chosen_chinese_font, "mono": chosen_mono_font}

# 设置应用主题
def apply_theme(app, dark_mode=True):
    global DARK_MODE
    DARK_MODE = dark_mode
    
    colors = Colors.current()
    
    # 创建调色板
    palette = QPalette()
    
    # 设置基本颜色
    palette.setColor(QPalette.Window, QColor(colors['bg_primary']))
    palette.setColor(QPalette.WindowText, QColor(colors['text_primary']))
    palette.setColor(QPalette.Base, QColor(colors['bg_secondary']))
    palette.setColor(QPalette.AlternateBase, QColor(colors['bg_tertiary']))
    palette.setColor(QPalette.ToolTipBase, QColor(colors['bg_tertiary']))
    palette.setColor(QPalette.ToolTipText, QColor(colors['text_primary']))
    palette.setColor(QPalette.Text, QColor(colors['text_primary']))
    palette.setColor(QPalette.Button, QColor(colors['bg_secondary']))
    palette.setColor(QPalette.ButtonText, QColor(colors['text_primary']))
    palette.setColor(QPalette.BrightText, QColor(colors['text_primary']))
    palette.setColor(QPalette.Link, QColor(colors['link']))
    palette.setColor(QPalette.Highlight, QColor(colors['accent']))
    palette.setColor(QPalette.HighlightedText, QColor('#ffffff'))
    
    # 设置禁用状态的颜色
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors['text_secondary']))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors['text_secondary']))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors['text_secondary']))
    
    # 应用调色板
    app.setPalette(palette)
    
    # 创建全局样式表
    stylesheet = f"""
    QMainWindow, QDialog {{
        background-color: {colors['bg_primary']};
        color: {colors['text_primary']};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {colors['border']};
        background-color: {colors['bg_secondary']};
        border-radius: 6px;
    }}
    
    QTabBar::tab {{
        background-color: {colors['bg_tertiary']};
        color: {colors['text_secondary']};
        padding: 8px 12px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {colors['bg_secondary']};
        color: {colors['text_primary']};
        border-bottom: 2px solid {colors['accent']};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {colors['highlight']};
    }}
    
    QPushButton {{
        background-color: {colors['bg_tertiary']};
        color: {colors['text_primary']};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        min-height: 32px;
        font-weight: 500;
    }}
    
    QPushButton:hover {{
        background-color: {colors['highlight']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['accent']};
        color: white;
    }}
    
    QPushButton:disabled {{
        background-color: {colors['bg_tertiary']};
        color: {colors['text_secondary']};
    }}
    
    QLineEdit {{
        background-color: {colors['bg_tertiary']};
        color: {colors['text_primary']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 8px;
        selection-background-color: {colors['accent']};
    }}
    
    QTextEdit, QTextBrowser {{
        background-color: {colors['bg_secondary']};
        color: {colors['text_primary']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 8px;
        selection-background-color: {colors['accent']};
        selection-color: white;
    }}
    
    QLabel {{
        color: {colors['text_primary']};
    }}
    
    QTreeWidget {{
        background-color: {colors['bg_secondary']};
        alternate-background-color: {colors['bg_tertiary']};
        color: {colors['text_primary']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        outline: none;  /* 移除焦点轮廓 */
    }}
    
    QTreeWidget::item {{
        padding: 6px;
        border-radius: 4px;
    }}
    
    QTreeWidget::item:selected {{
        background-color: {colors['accent']};
        color: white;
        outline: none;  /* 移除选中项的焦点轮廓 */
    }}
    
    QTreeWidget::item:hover {{
        background-color: {colors['highlight']};
    }}
    
    /* 明确移除所有焦点轮廓 */
    QTreeWidget::item:focus {{
        outline: none;
    }}
    
    QScrollBar:vertical {{
        background-color: {colors['bg_secondary']};
        width: 14px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors['scrollbar']};
        min-height: 20px;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {colors['accent']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {colors['bg_secondary']};
        height: 14px;
        margin: 0px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {colors['scrollbar']};
        min-width: 20px;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {colors['accent']};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    QToolButton {{
        background-color: transparent;
        border: none;
        border-radius: 4px;
        padding: 4px;
    }}
    
    QToolButton:hover {{
        background-color: {colors['highlight']};
    }}
    
    QCheckBox {{
        color: {colors['text_primary']};
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {colors['border']};
        background-color: {colors['bg_tertiary']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {colors['checkbox']};
        border: 1px solid {colors['checkbox']};
    }}
    
    QCheckBox::indicator:unchecked:hover {{
        border: 1px solid {colors['checkbox']};
    }}
    
    /* 成功提示样式 */
    .success {{
        color: {colors['success']};
    }}
    
    /* 错误提示样式 */
    .error {{
        color: {colors['error']};
    }}
    
    /* 警告提示样式 */
    .warning {{
        color: {colors['warning']};
    }}
    """
    
    app.setStyleSheet(stylesheet)

class StudentIDDialog(QDialog):
    """学号输入对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入学号")
        self.resize(400, 150)
        self.setModal(True)
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加说明文本
        info_label = QLabel("请输入您的学号 (12位数字):")
        info_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(info_label)
        
        # 添加学号输入框
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("例如: 5270********")
        self.id_input.setMaxLength(12)
        self.id_input.setFocus()
        layout.addWidget(self.id_input)
        
        # 添加错误提示标签(初始隐藏)
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.current()['error']};")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # 添加格式化显示标签
        self.formatted_label = QLabel()
        self.formatted_label.setStyleSheet(f"color: {Colors.current()['accent']}; font-size: 14px;")
        layout.addWidget(self.formatted_label)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # 连接信号
        self.id_input.textChanged.connect(self.update_formatted_display)
    
    def update_formatted_display(self):
        """更新格式化显示"""
        student_id = self.id_input.text().strip()
        if len(student_id) == 12 and student_id.isdigit():
            formatted = format_student_id(student_id)
            self.formatted_label.setText(f"格式化显示: {formatted}")
            self.formatted_label.setStyleSheet(f"color: {Colors.current()['success']}; font-size: 14px;")
        else:
            self.formatted_label.setText("")
    
    def validate_and_accept(self):
        """验证学号是否有效，有效则接受"""
        student_id = self.id_input.text().strip()
        
        if not is_valid_student_id(student_id):
            self.error_label.setText("错误: 学号必须是12位数字")
            self.error_label.setVisible(True)
            self.id_input.setFocus()
            return
        
        self.accept()
    
    def get_student_id(self):
        """获取输入的学号"""
        return self.id_input.text().strip()

class ThemeToggleWidget(QWidget):
    """主题切换组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = QApplication.instance()
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # 暗色/浅色模式图标
        self.theme_toggle = QCheckBox("暗色模式")
        self.theme_toggle.setChecked(DARK_MODE)
        self.theme_toggle.setStyleSheet(f"""
            QCheckBox {{
                font-size: 14px;
                font-weight: bold;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {Colors.current()['border']};
                background-color: {Colors.current()['bg_tertiary']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {Colors.current()['checkbox']};
                border: 1px solid {Colors.current()['checkbox']};
            }}
            
            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid {Colors.current()['checkbox']};
            }}
        """)
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        
        layout.addWidget(self.theme_toggle)
        self.setLayout(layout)
    
    def toggle_theme(self, state):
        apply_theme(self.app, state == Qt.Checked)
        self.theme_toggle.setText("暗色模式" if DARK_MODE else "浅色模式")
        # 更新复选框样式以匹配新主题
        self.theme_toggle.setStyleSheet(f"""
            QCheckBox {{
                font-size: 14px;
                font-weight: bold;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {Colors.current()['border']};
                background-color: {Colors.current()['bg_tertiary']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {Colors.current()['checkbox']};
                border: 1px solid {Colors.current()['checkbox']};
            }}
            
            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid {Colors.current()['checkbox']};
            }}
        """)
        
        # 通知主窗口更新树控件样式
        main_window = self.parent()
        while main_window and not isinstance(main_window, QMainWindow):
            main_window = main_window.parent()
        
        if main_window and hasattr(main_window, 'update_assignments_tree_style'):
            main_window.update_assignments_tree_style()
        
        # 同样更新任务树样式
        if main_window and hasattr(main_window, 'task_tree'):
            task_tree = main_window.task_tree
            colors = Colors.current()
            task_tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: {colors['bg_secondary']};
                    alternate-background-color: {colors['bg_tertiary']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['border']};
                    border-radius: 6px;
                    outline: none;
                }}
                
                QTreeWidget::item {{
                    padding: 6px;
                    border-radius: 4px;
                }}
                
                QTreeWidget::item:selected {{
                    background-color: {colors['accent']};
                    color: white;
                }}
                
                QTreeWidget::item:hover {{
                    background-color: {colors['highlight']};
                }}
            """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("CodeSentry")
        self.setWindowIcon(QIcon("arrow.ico"))  # 设置窗口图标
        self.resize(1500, 800)  # 增加窗口宽度
        
        # 全局变量
        self.current_assignment = None
        self.current_task = None
        self.test_point_details = {}  # 存储测试点详情的字典
        self.full_result_text = ""  # 存储完整的测试结果文本
        self.fonts = None  # 存储字体信息
        
        # 尝试切换到脚本或可执行文件所在目录
        try:
            if getattr(sys, 'frozen', False):  # 如果是EXE运行
                script_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:  # Python运行时
                script_dir = os.path.dirname(os.path.abspath(__file__))
            
            print(f"MainWindow中获取的脚本目录: {script_dir}")
            
            # 切换到脚本目录
            current_dir = os.getcwd()
            print(f"切换目录前的当前目录: {current_dir}")
            
            if current_dir != script_dir:
                os.chdir(script_dir)
                print(f"已切换到脚本目录: {os.getcwd()}")
            else:
                print("当前目录已经是脚本目录，无需切换")
            
            print(f"当前目录内容: {os.listdir()}")
        except Exception as e:
            error_msg = f"切换目录时出错: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            QMessageBox.critical(None, "错误", error_msg)
        
        # 获取所有作业文件夹
        self.assignment_folders = get_all_assignment_folders()
        print(f"MainWindow中获取的作业文件夹列表: {self.assignment_folders}")
        
        # 如果没有找到作业文件夹，尝试通过绝对路径查找
        if not self.assignment_folders:
            print("未通过常规方法找到作业文件夹，尝试备选方法...")
            try:
                # 检查与可执行文件相同目录下的特定文件夹
                if getattr(sys, 'frozen', False):  # 如果是EXE运行
                    base_dir = os.path.dirname(os.path.abspath(sys.executable))
                else:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                
                print(f"检查基础目录: {base_dir}")
                # 手动检查目录中的文件夹
                for item in os.listdir(base_dir):
                    item_path = os.path.join(base_dir, item)
                    if os.path.isdir(item_path):
                        if item.startswith('assignment') or item.startswith('challenge'):
                            print(f"手动找到作业文件夹: {item}")
                            # 将文件夹添加到列表
                            self.assignment_folders.append(item)
                
                # 对文件夹列表排序
                if self.assignment_folders:
                    def sort_key(folder):
                        match = re.search(r'(\d+)', folder)
                        if match:
                            number = int(match.group(1))
                        else:
                            number = 0
                        
                        # assignment优先，然后按数字排序
                        if folder.startswith('assignment'):
                            return (0, number)
                        else:
                            return (1, number)
                    
                    self.assignment_folders.sort(key=sort_key)
                    print(f"通过备选方法找到作业文件夹: {self.assignment_folders}")
            except Exception as e:
                print(f"备选方法查找作业文件夹出错: {str(e)}")
                traceback.print_exc()
        
        # 创建中央部件
        central_widget = QWidget()
        
        # 创建主布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 主题切换组件
        self.theme_toggle = ThemeToggleWidget()
        left_layout.addWidget(self.theme_toggle)
        
        # 添加分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separator)
        
        # 作业列表
        assignments_label = QLabel("Folders")
        assignments_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #a5e6dc;
                font-size: 24px;
                margin-bottom: 2px;
                font-family: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', monospace;
            }
        """)
        left_layout.addWidget(assignments_label)
        
        # 创建作业按钮区域
        if self.assignment_folders:
            # 使用树形控件代替按钮列表，以获得更紧凑的布局
            self.assignments_tree = QTreeWidget()
            self.assignments_tree.setHeaderHidden(True)
            self.assignments_tree.setAlternatingRowColors(True)
            self.assignments_tree.setAnimated(True)
            
            # 设置更紧凑的样式 - 这里只设置初始样式，后续会在主题切换时更新
            self.update_assignments_tree_style()
            
            # 添加作业文件夹到树控件
            for folder in self.assignment_folders:
                item = QTreeWidgetItem([folder])
                self.assignments_tree.addTopLevelItem(item)
            
            # 连接点击事件
            self.assignments_tree.itemClicked.connect(lambda item: self.update_task_list(item.text(0)))
            
            # 添加到布局中，并设置适当的高度
            left_layout.addWidget(self.assignments_tree)
            self.assignments_tree.setFixedHeight(150)
        else:
            no_assignment_label = QLabel("未找到作业文件夹")
            no_assignment_label.setStyleSheet(f"color: {Colors.current()['error']};")
            left_layout.addWidget(no_assignment_label)
            # 显示错误消息框
            QMessageBox.warning(None, "警告", "未找到作业文件夹，请确保程序位于正确目录！")
        
        # 添加分割线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separator2)
        
        # 题目列表
        tasks_label = QLabel("Questions")
        tasks_label.setStyleSheet(f"font-weight: bold; color: {Colors.current()['title_2']}; font-size: 24px; margin-bottom: 2px; font-family: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', monospace;")
        left_layout.addWidget(tasks_label)
        
        # 创建题目列表部件
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderHidden(True)
        self.task_tree.setAlternatingRowColors(True)
        self.task_tree.itemClicked.connect(self.on_task_clicked)
        self.task_tree.setAnimated(True)
        left_layout.addWidget(self.task_tree)
        
        # 添加垂直空白区域，使"一键打包"按钮位于底部
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        left_layout.addItem(vertical_spacer)
        
        # 添加分割线
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separator3)
        
        # 添加一键打包按钮
        self.package_button = QPushButton("Package")
        self.package_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7bc6ff, stop:1 #c1e192);
                color: white;
                font-weight: normal;
                padding: 12px;
                border-radius: 6px;
                min-height: 45px;
                font-size: 30px;
                border: none;
                font-family: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', 'Cascadia Code', monospace;
            }}
            
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4fc79b, stop:1 #52f6c9);
            }}
            
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2fa67b, stop:1 #32d6a9);
            }}
        """)
        self.package_button.clicked.connect(self.on_package_button_clicked)
        left_layout.addWidget(self.package_button)
        
        # 设置左侧面板
        left_panel.setLayout(left_layout)
        left_panel.setFixedWidth(250)  # 稍微减小左侧面板宽度，为右侧腾出空间
        
        # 创建右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 结果标题
        results_header = QWidget()
        results_header_layout = QHBoxLayout()
        results_header_layout.setContentsMargins(0, 0, 0, 10)
        
        results_label = QLabel("Result")
        results_label.setStyleSheet(f"font-weight: bold; color: {Colors.current()['title_3']}; font-size: 30px; margin-bottom: 0px; font-family: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', monospace;")
        results_header_layout.addWidget(results_label)
        
        results_header_layout.addStretch()
        
        results_header.setLayout(results_header_layout)
        right_layout.addWidget(results_header)
        
        # 结果显示区域
        self.result_text = QTextBrowser()
        self.result_text.setOpenExternalLinks(False)  # 不打开外部链接
        self.result_text.setReadOnly(True)
        
        # 设置等宽字体，确保分隔线能正确对齐显示
        chosen_font = None
        modern_fonts = ["JetBrains Mono", "Cascadia Code", "Fira Code", "Consolas", "Courier New"]
        for font_name in modern_fonts:
            font = QFont(font_name, 10)
            if font.exactMatch():
                chosen_font = font_name
                break
        
        if not chosen_font:
            chosen_font = "Monospace"
            font = QFont(chosen_font, 10)
            font.setStyleHint(QFont.Monospace)
        
        self.result_text.setFont(font)
	
        # 确保链接可点击
        self.result_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        self.result_text.anchorClicked.connect(self.on_test_point_link_clicked)
        right_layout.addWidget(self.result_text)
        
        # 设置右侧面板
        right_panel.setLayout(right_layout)
        right_panel.setMinimumWidth(1200)  # 设置右侧面板最小宽度，确保能显示长分隔线
        
        # 添加面板到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # 设置中央部件的布局
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 添加初始提示
        colors = Colors.current()
        welcome_html = f"""
        <div style="text-align: center; margin-top: 100px;">
            <h2 style="color: {colors['accent']};">欢迎使用代码检查系统</h2>
            <p style="font-size: 14px; margin-bottom: 30px;">请从左侧选择一个作业文件夹开始</p>
            <div style="color: {colors['text_secondary']}; font-size: 12px;">
                <p>• 选择作业文件夹后，可以在左侧题目列表中选择题目进行测试</p>
                <p>• 测试结果会显示在此区域</p>
                <p>• 点击"查看测试点详情"可以展开或收起详细信息</p>
                <p>• 使用底部的"一键打包"按钮可以快速打包作业文件</p>
            </div>
        </div>
        """
        self.result_text.setHtml(welcome_html)
        
        # 如果找到了作业文件夹，自动更新题目列表
        if self.assignment_folders:
            # 使用最新的作业文件夹
            latest_folder = get_latest_assignment_folder()
            if latest_folder:
                self.update_task_list(latest_folder)
    
    def update_task_list(self, assignment_path):
        """更新题目列表"""
        # 确保使用绝对路径
        self.current_assignment = os.path.abspath(assignment_path)
        self.task_tree.clear()
        
        # 更新窗口标题
        self.setWindowTitle(f"CodeSentry - {assignment_path}")
        
        # 切换到作业目录
        original_dir = os.getcwd()
        os.chdir(self.current_assignment)
        
        # 获取该作业下的所有题目文件夹
        folders = get_folders_by_pattern()
        
        # 添加题目到树形部件
        for folder in sorted(folders):
            item = QTreeWidgetItem([folder])
            self.task_tree.addTopLevelItem(item)
        
        # 恢复原始目录
        os.chdir(original_dir)
        
        # 清空结果文本
        self.result_text.clear()
        self.result_text.append(f"<span style='color:#666;'>已选择作业文件夹: {assignment_path}</span>")
        self.result_text.append("<span style='color:#666;'>请在左侧选择一个题目进行测试</span>")
    
    def on_task_clicked(self, item, column):
        """当题目被点击时"""
        self.current_task = item.text(0)
        self.run_task(self.current_task)
    
    def on_test_point_link_clicked(self, url):
        """当测试点链接被点击时"""
        try:
            url_str = url.toString()
            path = url.path()
            
            # 尝试从path中提取测试点号
            test_point_match = re.search(r'test_point:/?/?(\d+)', path)
            if test_point_match:
                test_point = int(test_point_match.group(1))
                self.process_test_point(test_point)
                return
            
            # 如果从path提取失败，尝试从URL字符串提取
            if url_str:
                test_point_match = re.search(r'test_point:/?/?(\d+)', url_str)
                if test_point_match:
                    test_point = int(test_point_match.group(1))
                    self.process_test_point(test_point)
                    return
            
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理链接点击时出错: {str(e)}")
    
    def process_test_point(self, test_point):
        """处理测试点详情"""
        
        if not self.current_task or not self.current_assignment:
            return
        
        # 确保使用绝对路径
        assignment_path = os.path.abspath(self.current_assignment)
        
        # 切换详情展示状态
        if test_point in self.test_point_details:
            self.test_point_details[test_point]['expanded'] = not self.test_point_details[test_point]['expanded']
        else:
            # 运行测试用例，获取详情
            try:
                # 运行测试用例
                result = run_test_case(self.current_task, test_point, assignment_path)
	
                # 使用修改后的display_test_case_details函数获取格式化的详情信息
                detailed_info = display_test_case_details(*result)
                
                # 保存测试点详情
                self.test_point_details[test_point] = {
                    'content': detailed_info,
                    'expanded': True
                }
            except Exception as e:
                self.test_point_details[test_point] = {
                    'content': f"获取详情失败: {str(e)}",
                    'expanded': True
                }
        
        # 更新显示
        self.update_display()
    
    def update_display(self):
        """更新结果显示，重新构建整个HTML内容"""
        
        # 保存当前滚动位置
        scrollbar = self.result_text.verticalScrollBar()
        current_scroll_position = scrollbar.value()
        
        # 构建完整的HTML内容，而不是逐行append
        html_content = []
        
        # 添加CSS样式，确保代码区域有足够的宽度并正确显示
        # 根据当前主题选择适当的颜色
        colors = Colors.current()
        
        # 获取等宽字体
        mono_font = "Consolas, monospace"
        if hasattr(self, 'fonts') and self.fonts and 'mono' in self.fonts:
            mono_font = f"{self.fonts['mono']}, Consolas, monospace"
        
        html_content.append(f"""
        <style>
            body {{
                font-family: {self.fonts['chinese'] if hasattr(self, 'fonts') and self.fonts and 'chinese' in self.fonts else 'sans-serif'}, system-ui;
            }}
            .code-container {{
                font-family: {mono_font};
                white-space: pre;
                overflow-x: auto;
                min-width: 1000px;
                width: 100%;
                color: {colors['text_primary']};
                background-color: {colors['bg_secondary']};
                padding: 12px;
                border-radius: 6px;
                border: 1px solid {colors['border']};
            }}
            .separator-line {{
                white-space: nowrap;
                font-family: {mono_font};
                width: 100%;
                color: {colors['text_secondary']};
            }}
            .detail-container {{
                margin-left: 20px; 
                padding: 15px; 
                border-left: 3px solid {colors['accent']}; 
                background-color: {colors['bg_tertiary']};
                border-radius: 6px;
                margin-top: 10px;
                margin-bottom: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }}
            a {{
                color: {colors['accent']};
                text-decoration: none;
                font-weight: bold;
                transition: color 0.2s;
            }}
            a:hover {{
                color: {colors['accent_alt']};
                text-decoration: underline;
            }}
            pre {{
                margin: 0;
                font-family: {mono_font};
            }}
        </style>
        """)
        
        # 解析并重构HTML内容
        html_lines = self.full_result_text.split('\n')
        for line in html_lines:
            # 处理测试点链接 - 匹配链接，不论是否有箭头
            test_point_match = re.search(r'<a href="test_point:(\d+)">查看测试点 (\d+) 详情( ▶)?</a>', line)
            
            if test_point_match:
                test_point = int(test_point_match.group(1))
                
                # 创建链接，并添加状态指示
                if test_point in self.test_point_details:
                    # 替换链接文本，添加状态指示
                    old_link = test_point_match.group(0)
                    indicator = "▼" if self.test_point_details[test_point]['expanded'] else "▶"
                    # 确保每个链接后面有<br/>标签
                    if '<br/>' in line:
                        new_link = f'<a href="test_point:{test_point}">查看测试点 {test_point} 详情 {indicator}</a><br/>'
                        line = line.replace(old_link + '<br/>', new_link)
                    else:
                        new_link = f'<a href="test_point:{test_point}">查看测试点 {test_point} 详情 {indicator}</a><br/>'
                        line = line.replace(old_link, new_link)
                else:
                    # 如果测试点不在详情字典中，确保它有箭头和换行
                    old_link = test_point_match.group(0)
                    if " ▶" not in old_link:
                        new_link = f'<a href="test_point:{test_point}">查看测试点 {test_point} 详情 ▶</a>'
                        line = line.replace(old_link, new_link)
                    if '<br/>' not in line:
                        line = line + '<br/>'
            
            # 特殊处理分隔线
            elif re.match(r'^-{10,}$', line):
                # 将长的分隔线放在一个特殊类中，确保不被折行
                line = f'<div class="separator-line">{line}</div>'
            
            # 处理代码段（标准输出、预期输出等）
            elif line.startswith('<pre>') and '</pre>' in line:
                # 将pre内容包装在代码容器中
                line = line.replace('<pre>', '<pre class="code-container">')
            
            # 添加到HTML内容
            html_content.append(line)
            
            # 如果是测试点链接行且测试点详情已展开，则添加详情内容
            if test_point_match:
                test_point = int(test_point_match.group(1))
                if test_point in self.test_point_details and self.test_point_details[test_point]['expanded']:
                    # 添加详情内容，不需要额外的换行，因为链接后已有<br/>
                    
                    # 使用CSS类控制详情容器样式
                    html_content.append('<div class="detail-container">')
                    
                    # 处理详情内容，确保HTML特殊字符被转义
                    content_text = self.test_point_details[test_point]['content']
                    # 转义<, >, &等特殊字符，防止被误解为HTML标签
                    content_text = content_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    
                    # 特殊处理详情内容中的分隔线
                    content_lines = content_text.split('\n')
                    processed_content = []
                    for content_line in content_lines:
                        if re.match(r'^-{10,}$', content_line):
                            # 将分隔线标记为不换行
                            processed_content.append(f'<span style="white-space: nowrap;">{content_line}</span>')
                        else:
                            processed_content.append(content_line)
                    
                    content_text = '\n'.join(processed_content)
                    
                    # 将内容包装在pre标签中，保持格式
                    html_content.append(f'<pre class="code-container">{content_text}</pre>')
                    
                    html_content.append('</div>')
        
        # 将所有内容连接成一个HTML字符串
        full_html = "\n".join(html_content)
        
        # 使用setHtml()方法一次性设置所有内容，确保HTML被正确解析
        self.result_text.clear()
        self.result_text.setHtml(full_html)
        
        # 尝试恢复滚动位置，调整策略让焦点尽量保持在当前测试点上
        QTimer.singleShot(1, lambda: self.restore_scroll_position(current_scroll_position))
        
    
    def restore_scroll_position(self, position):
        """恢复滚动条位置，并根据情况进行调整"""
        scrollbar = self.result_text.verticalScrollBar()
        # 获取当前内容高度
        max_value = scrollbar.maximum()
        
        # 如果内容变长，尝试调整位置，避免一直回到顶部
        if position > 0:
            # 设置滚动位置，略有偏移以确保用户能看到变化
            scrollbar.setValue(min(position, max_value))
    
    def run_task(self, task):
        """运行测试任务"""
        # 清空之前的结果和测试点详情
        self.result_text.clear()
        self.test_point_details.clear()
        self.full_result_text = ""
        
        if not self.current_assignment or not task:
            return
        
        
        try:
            # 切换到作业目录
            original_dir = os.getcwd()
            os.chdir(self.current_assignment)
	
            # 运行测试
            judger_path = os.path.join(os.getcwd(), "judger_batch.py")
            
            # 如果当前目录没找到，尝试在上级目录查找
            if not os.path.exists(judger_path):
                judger_path = os.path.join(os.path.dirname(os.getcwd()), "judger_batch.py")
            
            # 再找不到的话，直接在当前工作目录找
            if not os.path.exists(judger_path):
                judger_path = "judger_batch.py"
	
            if not os.path.exists(judger_path):
                # 使用auto_judger中的check_all_assignments函数可能的上下文
                script_dir = os.path.dirname(os.path.abspath(__file__))
                judger_path = os.path.join(script_dir, self.current_assignment, "judger_batch.py")
            
            if not os.path.exists(judger_path):
                # 尝试直接运行命令
                command = ["python", "-T", task]
                result = run_subprocess_no_window(command, capture_output=True, text=True, encoding='utf-8')
                stdout = result.stdout
                stderr = result.stderr
            else:
                # 运行判题器获取结果
                command = ["python", judger_path, "-T", task]
                
                result = run_subprocess_no_window(command, capture_output=True, text=True, encoding='utf-8')
	
                # 检查输出
                stdout = result.stdout
                stderr = result.stderr
            
            # 恢复原始目录
            os.chdir(original_dir)
            
            # 收集需要显示的文本行
            text_lines = []
            
            if stderr:
                text_lines.append(f"<pre style='color:red;'>{stderr}</pre>")
            
            # 检查所有得分是否都是10分
            scores = re.findall(r'\[SCORE\] (\d+)', stdout)
            
            all_correct = scores and all(int(score) == 10 for score in scores)
            
            # 显示结果
            if stdout:
                if all_correct:
                    text_lines.append("<span style='color:green; font-weight:bold;'>🎉 恭喜你，全部做对了！</span>")
                else:
                    text_lines.append("<span style='color:red; font-weight:bold;'>😢 还需要改进</span>")
                    
                    # 显示详细结果
                    text_lines.append("<pre>" + stdout + "</pre>")
                    
                    # 找出失败的测试点
                    test_points = re.findall(r'\[TEST POINT (\d+)\].*?\[SCORE\] (\d+)', stdout, re.DOTALL)
		
                    for test_point, score in test_points:
                        if int(score) != 10:
                            # 使用简单的路径格式，避免URL解析问题，并添加初始的箭头指示符
                            test_point_link = f'<a href="test_point:{test_point}">查看测试点 {test_point} 详情 ▶</a><br/>'
                            text_lines.append(test_point_link)
            else:
                text_lines.append("<span style='color:red; font-weight:bold;'>❌ 未获取到判题结果</span>")
                
                # 尝试自行运行测试
                text_lines.append("<span style='color:blue;'>正在尝试自行运行测试...</span>")
                try:
                    # 使用auto_judger中的函数自行测试
                    assigned_folders = [task]
                    
                    # 获取脚本的绝对路径目录
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    assignment_path = os.path.join(script_dir, self.current_assignment)
                    
                    # 保存标准输出以便捕获
                    original_stdout = sys.stdout
                    from io import StringIO
                    captured_output = StringIO()
                    sys.stdout = captured_output
                    
                    # 调用check_all_assignments
                    check_all_assignments(assigned_folders, assignment_path)
                    
                    # 恢复标准输出
                    sys.stdout = original_stdout
                    output = captured_output.getvalue()
                    
                    if output:
                        text_lines.append("<pre>" + output + "</pre>")
                    else:
                        text_lines.append("<span style='color:red;'>未获取到测试输出</span>")
                        
                except Exception as e:
                    text_lines.append(f"<span style='color:red;'>自行运行测试失败: {str(e)}</span>")
            
            # 保存完整的原始结果文本
            self.full_result_text = "\n".join(text_lines)
            
            # 使用setHtml一次性设置HTML内容，而不是逐行append
            self.result_text.clear()
            self.result_text.setHtml(self.full_result_text)
            
        except Exception as e:
            self.result_text.clear()
            self.result_text.append(f"<span style='color:red;'>运行测试时出错: {str(e)}</span>")
            # 恢复原始目录
            if 'original_dir' in locals():
                os.chdir(original_dir)

    def on_package_button_clicked(self):
        """处理一键打包按钮点击事件"""
        if not self.current_assignment:
            QMessageBox.warning(self, "警告", "请先选择一个作业文件夹")
            return
        
        try:
            # 获取学生学号
            student_id = None
            try:
                # 静默获取，不使用交互对话框
                config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_config.txt")
                if os.path.exists(config_file):
                    with open(config_file, "r") as f:
                        student_id = f.read().strip()
                    if not is_valid_student_id(student_id):
                        student_id = None
            except Exception as e:
                print(f"无法自动获取学号: {str(e)}")
                student_id = None
            
            # 如果没有获取到有效学号，则弹出输入对话框
            if not student_id:
                print("打开学号输入对话框")
                dialog = StudentIDDialog(self)
                if dialog.exec_() == QDialog.Accepted:
                    student_id = dialog.get_student_id()
                    
                    # 保存学号到配置文件
                    try:
                        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_config.txt")
                        with open(config_file, "w") as f:
                            f.write(student_id)
                    except Exception as e:
                        print(f"保存学号时出错: {str(e)}")
                else:
                    return
            
            # 确保使用绝对路径
            assignment_path = os.path.abspath(self.current_assignment)
            
            # 显示打包中提示，但不强制更新UI
            self.result_text.append("<span style='color:blue;'>正在打包作业文件...</span>")
            
            # 创建打包文件
            zip_path = create_zip_package(assignment_path, student_id)
            
            if zip_path:
                self.result_text.append(f"<span style='color:green; font-weight:bold;'>打包成功! 文件已保存为: {zip_path}</span>")
                QMessageBox.information(self, "打包成功", f"作业已成功打包为:\n{zip_path}")
            else:
                self.result_text.append("<span style='color:red; font-weight:bold;'>打包失败!</span>")
                QMessageBox.critical(self, "打包失败", "未能成功打包作业文件。请查看详情。")
        
        except Exception as e:
            error_msg = f"打包过程中出错: {str(e)}"
            self.result_text.append(f"<span style='color:red;'>{error_msg}</span>")
            QMessageBox.critical(self, "错误", error_msg)

    def update_assignments_tree_style(self):
        """更新作业列表树控件的样式，根据当前主题"""
        if hasattr(self, 'assignments_tree'):
            colors = Colors.current()
            self.assignments_tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: {colors['bg_secondary']};
                    alternate-background-color: {colors['bg_tertiary']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['border']};
                    border-radius: 6px;
                    outline: none;
                }}
                
                QTreeWidget::item {{
                    padding: 3px 6px;
                    border-radius: 4px;
                    min-height: 22px;
                }}
                
                QTreeWidget::item:selected {{
                    background-color: {colors['accent']};
                    color: white;
                }}
                
                QTreeWidget::item:hover {{
                    background-color: {colors['highlight']};
                }}
            """)

def main():
    try:
        app = QApplication(sys.argv)
        
        # 设置应用字体
        try:
            fonts = set_app_fonts(app)
        except Exception as e:
            print(f"设置应用字体时出错: {str(e)}")
            print(traceback.format_exc())
        
        # 设置应用主题
        apply_theme(app, dark_mode=True)

        window = MainWindow()
        window.fonts = fonts  # 将字体信息传递给主窗口
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = f"程序启动出错: {str(e)}"
        
        # 尝试显示错误对话框
        try:
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
            QMessageBox.critical(None, "程序错误", error_msg)
        except:
            # 如果连错误对话框都无法显示，则写入错误日志
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(f"{error_msg}\n")
                f.write(traceback.format_exc())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"程序出错: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        
