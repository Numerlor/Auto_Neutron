setlocal
FOR /F "tokens=*" %%i in ('type .env') do SET %%i
IF NOT DEFINED VENV_DIR SET VENV_DIR=.venv
call ..\%VENV_DIR%\Scripts\activate.bat
python -OO -m PyInstaller Auto_Neutron.spec --upx-dir=%UPX_DIR%
endlocal