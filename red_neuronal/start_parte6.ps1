# Inicia la demostración; no pide credenciales ni abre conexiones MySQL.
param([ValidateRange(1024,65535)][int]$Port = 8007)
$ErrorActionPreference = 'Stop'
$parte6Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$parte6Root;$parte6Root/backend"
& "$env:USERPROFILE/.venvs/p6/Scripts/python.exe" -m uvicorn app.parte6:app --app-dir "$parte6Root/backend" --host 127.0.0.1 --port $Port
