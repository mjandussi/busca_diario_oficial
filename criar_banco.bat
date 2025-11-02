@echo off
echo Criando banco de dados decreto_test na porta 5433...
echo.

REM Tentar criar banco (porta 5433)
psql -U postgres -p 5433 -c "CREATE DATABASE decreto_test;"

echo.
echo Banco criado! Pressione qualquer tecla para sair.
pause
