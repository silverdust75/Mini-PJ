@echo off
rem 1. 아나콘다 경로 설정 (본인의 PC 환경에 맞게 자동 탐색)
set CONDAPATH=C:\Users\%USERNAME%\anaconda3
if not exist %CONDAPATH% set CONDAPATH=C:\ProgramData\anaconda3

rem 2. 아나콘다 활성화 스크립트 실행
call %CONDAPATH%\Scripts\activate.bat %CONDAPATH%

rem 3. 가상환경 활성화 (py39)
call conda activate py39

rem 4. 스트림릿 실행
cd /d "%~dp0"
streamlit run mini13.py

pause