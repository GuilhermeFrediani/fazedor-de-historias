@echo off
title FAZEDOR DE HISTORIAS - TE0 ^& JUCA Company
cd /d "C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de historias\fazedor_app" 2>nul
cd /d "C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app"
set PYTHON=C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=python
echo ============================================
echo   FAZEDOR DE HISTORIAS - TE0 ^& JUCA Company
echo   Servidor: http://127.0.0.1:8756
echo   (o navegador abre sozinho; deixe ESTA
echo    janela aberta enquanto trabalha)
echo   Para desligar: feche esta janela ou Ctrl+C
echo ============================================
"%PYTHON%" fazedor_app.py
pause
