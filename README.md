# SJTU C++ Homework Tool

本项目是专为上海交通大学《程序设计原理与方法》（2025 春）设计的图形化作业自动评测与打包工具，旨在简化测试流程，避免手动输入大量命令行。

## 0. 运行环境要求

确保以下条件满足，否则程序可能无法正常运行：

1. `CodeSentry.exe` **必须** 与 `assignment` 或 `challenge` 文件夹位于 **同一目录**。
2. 作业文件夹命名格式必须为 `assignmentX` 或 `challengeX`（其中 `X` 为正整数）。
3. `assignmentX` 或 `challengeX` 文件夹内 **必须** 包含作业子文件夹（例如 `1_xxx`）。
4. 每道题目的 **主文件名称** 必须为 `main.cpp`。

## 1. 使用方法

### a. Windows用户
1. **下载**  
   仅需下载 `CodeSentry.exe`，可在 [Release 页面](https://github.com/lxclxclxc-github/sjtu-cpp-homework-tool/releases/tag/v0.3.1) 获取。
   推荐下载`arrow.ico`，这是程序的图标。放在同一目录下即可。
3. **运行**  
   将 `CodeSentry.exe` 移动到合适路径后，**双击运行**。

### b. Mac用户
1. 下载`gui_judger.py`与`arrow.ico`(如果嫌麻烦，停在这一步也可以，直接运行py文件即可。)
2. 安装第三方库：pyinstaller
3. 确保已经安装了所有依赖库（在py文件一开始就都列出来了）
4. 在对应文件夹下命令行：`pyinstaller --noconsole --onefile --icon=arrow.ico --name=CodeSentry gui_judger.py`
5. 如果遇到pyqt5缺少sip的报错提示：更新最新版本的sip。详情自行上网查找。
6. 打包完成后，会在`dist/`文件夹下显示`CodeSentry.exe`，拖到原文件夹下即可。

## 2. 功能介绍

1. **代码检查**  
   在图形化界面中选择要检查的题目，一键运行评测。
2. **错误对比**  
   若发现错误，可查看正确输出与程序输出的详细比较。
3. **一键打包**  
   通过左下角的“打包”按钮，自动生成 `学号.zip` 格式的压缩文件。
4. 其它细节
   - 字体调整：`Ctrl+滚轮`
   - 窗口颜色：默认跟随系统
   - 字体更新：推荐 JetBrains Mono 与 微软雅黑 的搭配。如果没有下载，程序会按照其他默认字体显示。

![image](https://github.com/user-attachments/assets/8f05bcb4-a4a2-4b23-82d2-08698e39e853)

![image](https://github.com/user-attachments/assets/9fd6ce9e-3f2e-4dd9-a5c3-08287fd2da3d)

