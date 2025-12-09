@echo off
chcp 65001 >nul
title SVD GUI Viewer 一键打包工具
echo =============================================
echo       SVD GUI Viewer 一键打包工具
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
if exist SVD_Viewer.spec del /f /q SVD_Viewer.spec
echo [✓] 清理完成

:: 执行打包
echo [步骤5] 正在打包 svd_gui_viewer.py ...
echo [提示] 这可能需要几分钟，请耐心等待...
pyinstaller ^
--onefile ^
--noconsole ^
--name "SVD_Viewer" ^
--add-data "TLE987x.svd;." ^
--exclude-module numpy ^
--exclude-module pandas ^
--exclude-module matplotlib ^
--exclude-module PIL ^
svd_gui_viewer.py

if %errorlevel% neq 0 (
    echo [错误] 打包过程中出现问题，请检查上方日志！
    call deactivate
    pause
    exit /b
)

:: 退出虚拟环境
call deactivate

:: 显示文件大小
echo.
echo [步骤6] 检查生成的文件 ...
if exist "dist\SVD_Viewer.exe" (
    for %%I in (dist\SVD_Viewer.exe) do (
        set size=%%~zI
        set /a size_mb=!size! / 1048576
        echo [✓] 文件大小: !size_mb! MB (%%~zI 字节)
    )
) else (
    echo [错误] 未找到生成的 exe 文件！
)

echo =============================================
echo [完成] 打包成功！
echo 生成文件路径：dist\SVD_Viewer.exe
echo =============================================
echo.

:: 询问是否打开目录
set /p open_folder="是否打开输出目录？(Y/N): "
if /i "%open_folder%"=="Y" (
    explorer dist
)

pause
