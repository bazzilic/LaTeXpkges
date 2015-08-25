@echo off
python setup.py py2exe
rmdir build /s /q
del dist\w9xpopen.exe
