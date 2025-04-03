# SJTU C++ Homework Tool

本项目是专为上海交通大学《程序设计原理与方法》（2025 春）设计的图形化作业自动评测与打包工具，旨在简化测试流程，避免手动输入大量命令行。

## 0. 运行环境要求

确保以下条件满足，否则程序可能无法正常运行：

1. `CodeSentry.exe` **必须** 与 `assignment` 或 `challenge` 文件夹位于 **同一目录**。
2. 作业文件夹命名格式必须为 `assignmentX` 或 `challengeX`（其中 `X` 为正整数）。
3. `assignmentX` 或 `challengeX` 文件夹内 **必须** 包含作业子文件夹（例如 `1_xxx`）。
4. 每道题目的 **主文件名称** 必须为 `main.cpp`。

## 1. 使用方法

1. **下载**  
   仅需下载 `CodeSentry.exe`，可在 [Release 页面](https://github.com/lxclxclxc-github/sjtu-cpp-homework-tool/releases/tag/v0.2) 获取。
2. **运行**  
   将 `CodeSentry.exe` 移动到合适路径后，**双击运行**。

## 2. 功能介绍

1. **代码检查**  
   在图形化界面中选择要检查的题目，一键运行评测。
2. **错误对比**  
   若发现错误，可查看正确输出与程序输出的详细比较。
3. **一键打包**  
   通过左下角的“打包”按钮，自动生成 `学号.zip` 格式的压缩文件。

