#!/bin/bash
# Script para compilar la APK de NOVA AI en Linux/WSL/Mac
# Uso: bash compilar_apk.sh

set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  🏗️  Compilando NOVA AI Android..."
echo "============================================================"

# Verificar buildozer
if ! command -v buildozer &> /dev/null; then
    echo "❌ buildozer no instalado. Instala con:"
    echo "    pip install --user buildozer cython==0.29.36"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 1
fi

# Verificar Java
if ! command -v java &> /dev/null; then
    echo "❌ Java no instalado. Instala con:"
    echo "    sudo apt install openjdk-17-jdk"
    exit 1
fi

echo ""
echo "📦 Compilando APK debug..."
echo "(La primera vez tarda 30-60 minutos por la descarga del SDK Android)"
echo ""

buildozer android debug

echo ""
echo "============================================================"
echo "  ✅ ¡Listo! La APK está en:"
echo "============================================================"
ls -lh bin/*.apk 2>/dev/null || echo "(no se encontró APK — revisa errores arriba)"
echo ""
echo "📲 Para instalarla en tu móvil:"
echo "    1. Conecta el móvil por USB con depuración activada"
echo "    2. adb install bin/novaai-1.0-arm64-v8a_armeabi-v7a-debug.apk"
echo ""
echo "  O cópiala manualmente y ábrela en el explorador del móvil."
