[app]

# Nombre visible en el móvil
title = NOVA AI

# Nombre del paquete (debe ser único en Play Store si la subes)
package.name = novaai

# Dominio inverso (cualquier cosa que NO uses)
package.domain = org.novaai.android

# Carpeta con el código Python
source.dir = .

# Extensiones de archivos a incluir
source.include_exts = py,png,jpg,kv,atlas,json,ttf

# Archivo principal
source.main = main.py

# Versión
version = 1.0

# Requisitos Python
requirements = python3,kivy==2.3.0,certifi,urllib3,charset-normalizer,idna,requests,pyjnius,android,plyer

# Orientación
orientation = portrait

# Pantalla completa (0=no, 1=sí)
fullscreen = 0

# Icono y splash (opcional - pon tus PNGs en assets/)
#icon.filename = %(source.dir)s/assets/icon.png
#presplash.filename = %(source.dir)s/assets/splash.png

# Permisos Android pedidos al instalar
# Algunos se piden además en runtime
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, CAMERA, RECORD_AUDIO, CALL_PHONE, SEND_SMS, ACCESS_NETWORK_STATE

# API mínima y target
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Arquitecturas (ARM64 para móviles modernos, armeabi-v7a para viejos)
android.archs = arm64-v8a, armeabi-v7a

# Color y modo de splash
android.presplash_color = #1e1e2e

# Mostrar la consola en debug (ver logs con: adb logcat | grep python)
android.logcat_filters = *:S python:D

# Categoría
android.category = productivity

# === Configuración Buildozer ===
[buildozer]

log_level = 2
warn_on_root = 1
