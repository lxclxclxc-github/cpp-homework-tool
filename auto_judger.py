import os
import re
import subprocess
import sys

def get_latest_assignment_folder():
    # 获取当前目录下所有文件夹，筛选出以 "assignment" 开头的文件夹
    folders = [f for f in os.listdir() if os.path.isdir(f) and f.startswith('assignment')]
    
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
        user_input = input("请输入要执行的文件夹对应的正整数 (序号): \n输入 'a' 检查所有(all)题目或输入 'q' 退出: ")

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
            print(f"执行：python {judger_path} -T {selected_folder}")
            result = subprocess.run(["python", judger_path, "-T", selected_folder],
                                    capture_output=True, text=True)
            print(result.stdout)

            # 检查所有得分是否都是10分
            scores = re.findall(r'\[SCORE\] (\d+)', result.stdout)
            if scores and all(int(score) == 10 for score in scores):
                print("\n恭喜你，作对了！🎉😘✌️")
            else:print("\n啊偶，要不再看看😢😫🤯")

        else:
            print("无效的输入，未找到对应的文件夹")
        
        print("\n" + "="*50)  # 分隔线，使输出更清晰
    # 等待用户按 Enter 键后退出程序
    input("\n执行完毕。按 Enter 键退出...")

if __name__ == "__main__":
    main()
