[app]

title = NOVA AI
package.name = novaai
package.domain = org.novaai.android
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
source.main = main.py
version = 1.0

requirements = python3==3.11.6,kivy==2.3.0,plyer,requests,certifi,urllib3,charset-normalizer,idna

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, CAMERA, RECORD_AUDIO, CALL_PHONE, SEND_SMS, ACCESS_NETWORK_STATE

android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

android.presplash_color = #1e1e2e
android.logcat_filters = *:S python:D
android.category = productivity

[buildozer]

log_level = 2
warn_on_root = 1
