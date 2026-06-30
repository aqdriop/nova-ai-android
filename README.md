# 📱 NOVA AI Android — Port a móvil

App de IA que **actúa en tu Android con tu permiso**, igual que la versión PC.

> 💡 Compilar una APK Android desde Python con Kivy es un proceso técnico.
> Te dejo TODO listo, solo hace falta una máquina Linux/WSL/Mac para compilar.
> (En Windows puro NO se puede compilar directamente, pero la app SÍ se puede instalar después).

---

## 📂 Archivos en esta carpeta

| Archivo | Para qué |
|---|---|
| `main.py` | El código de la app (~750 líneas) |
| `buildozer.spec` | Configuración para compilar la APK |
| `README.md` | Esta guía |
| `assets/` | Icono y splash (opcional) |

---

## ✨ Funciones

- 💬 **Chat con IA**: Gemini, Groq u OpenAI
- ⚙️ **Configuración**: cambiar proveedor, modelo, API key
- 🔐 **Acciones con permiso** (popup ✅/❌ antes de cada acción):
  - 📄 Crear / leer / borrar archivos (en almacenamiento)
  - 🌐 Abrir URLs en navegador
  - 📱 Abrir apps por nombre de paquete (com.whatsapp, com.spotify.music...)
  - 📤 Compartir texto con otras apps
  - 📞 Llamar a un número
  - ☎️ Abrir el marcador
  - 💬 Preparar SMS
- 🔑 **Permisos bajo demanda**: NOVA solo pide el permiso justo cuando lo necesita

---

## 🛠️ Cómo compilar la APK (paso a paso)

### Opción A — Linux nativo o WSL (Windows Subsystem for Linux)

**1.** Instala Linux/WSL si estás en Windows:
```bash
wsl --install -d Ubuntu
```

**2.** En Ubuntu/Linux, instala las dependencias:
```bash
sudo apt update
sudo apt install -y python3 python3-pip git zip unzip openjdk-17-jdk \
    python3-venv autoconf libtool pkg-config zlib1g-dev libncurses-dev \
    libncursesw5-dev libtinfo6 cmake libffi-dev libssl-dev build-essential ccache
```

**3.** Instala Buildozer:
```bash
pip install --user buildozer cython==0.29.36
export PATH="$HOME/.local/bin:$PATH"
```

**4.** Copia esta carpeta a Linux y entra:
```bash
cd "android-nova"
```

**5.** Compila la APK (la primera vez tarda 30-60 min porque descarga el SDK Android):
```bash
buildozer android debug
```

**6.** ¡Listo! La APK estará en:
```
bin/novaai-1.0-arm64-v8a_armeabi-v7a-debug.apk
```

---

### Opción B — GitHub Actions (compilación en la nube, gratis)

Si no quieres instalar nada, puedes subir el proyecto a GitHub y compilar automáticamente.

**1.** Crea `.github/workflows/build-apk.yml` en tu repo:

```yaml
name: Build APK
on: [push, workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      - name: Compilar APK
        uses: ArtemSBulgakov/buildozer-action@v1
        with:
          command: buildozer android debug
          buildozer_version: stable
      - uses: actions/upload-artifact@v3
        with:
          name: NovaAI-APK
          path: bin/*.apk
```

**2.** Sube tu repo a GitHub → ve a la pestaña **Actions** → descarga la APK desde "Artifacts".

---

## 📲 Instalar la APK en tu móvil

1. Copia la APK a tu Android (USB, email, Drive...)
2. En el móvil: **Ajustes → Seguridad → Permitir instalar apps de orígenes desconocidos**
3. Abre el archivo .apk con el explorador de archivos
4. Pulsa "Instalar"
5. Abre **NOVA AI** desde el cajón de apps

---

## 🚀 Primer uso

1. Abre NOVA AI en tu móvil
2. Pulsa ⚙ arriba a la derecha
3. Elige proveedor (recomendado **Groq** — gratis y rápido)
4. Pega tu API Key
5. Pulsa **💾 Guardar configuración**
6. Vuelve atrás y empieza a hablar con NOVA

---

## 💡 Ejemplos para probar

| Le dices | NOVA propone |
|---|---|
| *"Créame un archivo notas.txt con mi lista de compras"* | Crear archivo (pide permiso de almacenamiento) |
| *"Abre WhatsApp"* | Abrir app `com.whatsapp` |
| *"Abre YouTube"* | Abrir URL `https://youtube.com` |
| *"Llama al 666123456"* | Pide permiso CALL_PHONE y llama |
| *"Manda un SMS a mi madre"* | Abre la app de SMS con el mensaje |
| *"Comparte 'hola mundo'"* | Abre el diálogo nativo de compartir |

---

## 🔐 Seguridad

- ✅ **NOVA nunca actúa sola** — cada acción tiene un popup con ✅/❌
- ✅ Los permisos Android se piden **en el momento exacto** (no al instalar todo de golpe)
- ✅ La API Key se guarda **local** en `app_storage_path()` (privado de la app)
- ✅ El chat NO se sincroniza a ninguna nube

---

## ⚠️ Limitaciones

- 🚫 NO puede tomar capturas de pantalla (Android lo bloquea por seguridad)
- 🚫 NO puede leer notificaciones de otras apps (necesita permisos especiales)
- 🚫 NO puede usar el micrófono todavía (próxima versión)
- 🚫 NO puede generar imágenes (próxima versión, con Pollinations)

---

## 🐞 Problemas comunes

| Problema | Solución |
|---|---|
| `buildozer` no se reconoce | `export PATH="$HOME/.local/bin:$PATH"` |
| Falla en `python-for-android` | Borra `.buildozer/` y vuelve a probar |
| APK instala pero crashea | Conecta el móvil por USB → `adb logcat | grep python` |
| Error de Java | Asegúrate de tener OpenJDK 17 (`java -version`) |

---

## 🛣️ Roadmap futuro

- 🎤 Reconocimiento de voz (botón micro)
- 🗣️ TTS para que NOVA hable
- 📷 Cámara integrada
- 🎨 Generación de imágenes (Pollinations)
- 🌗 Tema claro/oscuro
- 📚 Historial de chats persistente
