cd "C:\Users\OH\Desktop\MyScripts\Python\Private\taskbar-color-change-by-lang"
pyinstaller --onefile --paths="C:\Users\OH\Desktop\MyScripts\Python\Private\taskbar-color-change-by-lang\venv\Lib\site-packages" --icon="C:\Users\OH\Desktop\MyScripts\Python\Private\taskbar-color-change-by-lang\windows-11-change-taskbar-color.ico" --hidden-import=ctypes --hidden-import=win32api --hidden-import=win32con --hidden-import=pywin32 --noconsole --add-data "C:\Users\OH\Desktop\MyScripts\Python\Private\taskbar-color-change-by-lang\windows-11-change-taskbar-color.png;." "C:\Users\OH\Desktop\MyScripts\Python\Private\taskbar-color-change-by-lang\taskbar-color-change-by-lang.py"
move "dist\taskbar-color-change-by-lang.exe"
rd /s /q build
rd /s /q dist
del "taskbar-color-change-by-lang.spec"