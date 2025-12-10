@echo off
chcp 65001 >nul
title SVD GUI Viewer 便携版打包工具
echo =============================================
echo    SVD GUI Viewer 便携版打包工具
echo    (包含所有运行时依赖)
echo =============================================

:: 切换到当前脚本所在目录
cd /d %~dp0

:: 检查 Python 环境
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python!
    pause
    exit /b
)
echo [✓] Python 已安装

:: 创建虚拟环境
echo [步骤1] 创建虚拟环境 env ...
if not exist env (
    python -m venv env
    echo [✓] 虚拟环境创建成功
) else (
    echo [✓] 虚拟环境已存在
)

:: 激活虚拟环境
echo [步骤2] 激活虚拟环境 ...
call "%~dp0env\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [警告] 激活虚拟环境失败，继续执行后续步骤...
)

:: 安装 PyInstaller
echo [步骤3] 安装 PyInstaller ...
pip install -U pip >nul 2>nul
pip install pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] PyInstaller 安装失败！
    pause
    exit /b
)
echo [✓] PyInstaller 安装完成

:: 清理旧文件
echo [步骤4] 清理旧打包结果 ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist SVD_Viewer_portable.spec del /f /q SVD_Viewer_portable.spec
echo [✓] 清理完成

:: 执行打包 - 便携版（包含所有依赖）
echo [步骤5] 正在打包 svd_gui_viewer.py (便携版) ...
echo [提示] 这可能需要几分钟，请耐心等待...
pyinstaller ^
--onedir ^
--noconsole ^
--name "SVD_Viewer_portable" ^
--add-data "TLE987x.svd;." ^
--exclude-module numpy ^
--exclude-module pandas ^
--exclude-module matplotlib ^
--exclude-module PIL ^
--collect-all tkinter ^
--hidden-import xml.etree.ElementTree ^
svd_gui_viewer.py

if %errorlevel% neq 0 (
    echo [错误] 打包过程中出现问题，请检查上方日志！
    call deactivate
    pause
    exit /b
)

:: 退出虚拟环境
call deactivate

:: 显示文件夹大小
echo.
echo [步骤6] 检查生成的文件 ...
if exist "dist\SVD_Viewer_portable" (
    echo [✓] 便携版生成成功！
    echo [✓] 主程序: dist\SVD_Viewer_portable\SVD_Viewer_portable.exe
    echo [提示] 可以将整个 SVD_Viewer_portable 文件夹复制到其他电脑使用
) else (
    echo [错误] 未找到生成的文件夹！
)

echo =============================================
echo [完成] 打包成功！
echo 生成路径：dist\SVD_Viewer_portable\
echo 使用方法：复制整个文件夹到目标电脑即可运行
echo =============================================
echo.

:: 询问是否打开目录
set /p open_folder="是否打开输出目录？(Y/N): "
if /i "%open_folder%"=="Y" (
    explorer dist
)

pause
