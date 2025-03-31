import os
import re
import subprocess
import sys
import tempfile
import shutil

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
    # 导入judger_batch模块
    sys.path.insert(0, assignment_path)
    from judger_batch import input_name, output_name, exec_name, get_random_filename
    
    # 创建临时工作目录
    workdir = tempfile.mkdtemp()
    
    try:
        # 准备文件路径
        input_dir = os.path.join(assignment_path, 'data', task_folder)
        standard_dir = os.path.join(assignment_path, 'data', task_folder)
        source_dir = os.path.join(assignment_path, task_folder)
        
        main_dir = os.path.join(source_dir, exec_name[task_folder][0])
        exec_dir = os.path.join(workdir, exec_name[task_folder][1])
        
        # 编译代码
        compile_cmd = ['g++', main_dir, '-o', exec_dir, '-g', '-Wall', '--std=c++11']
        cp_pro = subprocess.run(compile_cmd, capture_output=True)
        
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
        with open(input_file, 'r') as f:
            input_content = f.read().strip()
        
        # 创建用户输出文件
        user_output_file = os.path.join(workdir, get_random_filename() + '.out')
        with open(input_file, 'r') as fin, open(user_output_file, 'w') as fout:
            try:
                subprocess.run(
                    [exec_dir], check=True, timeout=2,
                    stdin=fin, stdout=fout
                )
            except subprocess.TimeoutExpired:
                return False, "超时", "程序运行超时", input_content, None, None
            except subprocess.CalledProcessError as e:
                return False, "运行时错误", f"返回值: {e.returncode}", input_content, None, None
        
        # 读取用户输出和标准输出
        with open(user_output_file, 'r') as f:
            user_output_content = f.read().strip()
        with open(standard_file, 'r') as f:
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
    
    except ImportError:
        return False, "导入错误", "无法导入judger_batch模块", None, None, None
    finally:
        # 清理临时目录
        shutil.rmtree(workdir, ignore_errors=True)
        # 移除添加的路径
        if assignment_path in sys.path:
            sys.path.remove(assignment_path)

def display_test_case_details(success, msg, details, input_content, user_output, std_output):
    """显示测试案例的详细信息"""
    if not success:
        print(f"错误类型: {msg}")
        if details:
            print(f"详细信息: {details}")
        
        # 打印标准输入
        if input_content:
            print("\n标准输入:")
            print("-" * 40)
            print(input_content)
            print("-" * 40)
        
        # 打印用户输出和标准输出
        if user_output is not None and std_output is not None:
            print("\n你的输出:")
            print("-" * 40)
            print(user_output)
            print("-" * 40)
            print("\n标准输出:")
            print("-" * 40)
            print(std_output)
            print("-" * 40)

def check_all_assignments(folders, assignment_path):
    all_passed = True
    for folder in sorted(folders):  # 确保按序号顺序检查
        x_value = folder.split('_')[0]
        print(f"\n正在检查第 {x_value} 题...")

        judger_path = os.path.join(assignment_path, "judger_batch.py")
        result = subprocess.run(["python", judger_path, "-T", folder],
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
                    display_test_case_details(*result)
            
            all_passed = False
        print("="*50)
    if all_passed:
        print("\n🎉 太好啦，可以交作业啦！🎉")
    else:
        print("\n继续加油，马上就能完成啦！💪")
    
    return all_passed

def main():
    # 获取脚本或exe的绝对路径目录
    script_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    
    # 切换到脚本目录
    os.chdir(script_dir)
    
    # 1. 自动cd到最大后缀数字的 "assignment" 文件夹
    latest_folder = get_latest_assignment_folder()
    if not latest_folder:
        print("未找到 assignment 文件夹")
        input("按任意键退出...")
        return
    
    assignment_path = os.path.join(script_dir, latest_folder)
    os.chdir(assignment_path)

    
    # 2. 获取符合 "x_yyy" 格式的文件夹
    folders = get_folders_by_pattern()
    if not folders:
        print("未找到符合 '序号_名称' 格式的文件夹")
        input("按任意键退出...")
        return
    
    while True:
        # 3. 列出所有可选项
        print("可选的文件夹：")
        for folder in folders:
            x_value = folder.split('_')[0]  # 提取 x（即正整数）
            print(f"{x_value}: {folder}")

        # 4. 用户输入选择
        user_input = input("""\n输入题号（如1）检测特定题目\n输入 a 检测所有题目\n输入 q 退出系统\n请输入: """)

        # 检查是否退出
        if user_input.lower() == 'q':
            break

        # 检查是否要检查所有题目
        if user_input.lower() == 'a':
            check_all_assignments(folders, assignment_path)
            continue

        # 5. 查找并执行对应的文件夹
        selected_folder = None
        for folder in folders:
            if folder.startswith(user_input):
                selected_folder = folder
                break
    
        if selected_folder:
            judger_path = os.path.join(assignment_path, "judger_batch.py")
            result = subprocess.run(["python", judger_path, "-T", selected_folder],
                                    capture_output=True, text=True)
            

            # 检查所有得分是否都是10分
            scores = re.findall(r'\[SCORE\] (\d+)', result.stdout)
            all_correct = scores and all(int(score) == 10 for score in scores)
            
            if all_correct:
                print("\n恭喜你，作对了！🎉😘✌️")
            else:

                print(result.stdout)
                # 找出失败的测试点
                test_points = re.findall(r'\[TEST POINT (\d+)\].*?\[SCORE\] (\d+)', result.stdout, re.DOTALL)
                for test_point, score in test_points:
                    if int(score) != 10:
                        print(f"\nTEST POINT {test_point} 失败")
                        result = run_test_case(selected_folder, int(test_point), assignment_path)
                        display_test_case_details(*result)
        else:
            print("无效的输入，未找到对应的文件夹")
        
        print("\n" + "="*50)  # 分隔线，使输出更清晰
    # 等待用户按 Enter 键后退出程序
    input("\n执行完毕。按 Enter 键退出...")

if __name__ == "__main__":
    main()
