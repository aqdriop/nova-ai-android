# 📲 Cómo instalar NOVA AI en tu Android

> ⚠️ **IMPORTANTE**: Lo que descargaste (`main.py`, `buildozer.spec`...) es
> el **código fuente**, NO una app instalable. Antes hay que **compilar**
> una APK. Aquí están las 3 formas, de más fácil a más técnica.

---

## 🥇 OPCIÓN 1 — GitHub Actions (RECOMENDADA, gratis, sin instalar nada)

### Paso 1: Crear cuenta en GitHub
1. Ve a https://github.com/signup
2. Crea una cuenta gratis con tu email

### Paso 2: Crear un repositorio
1. Una vez logueado, pulsa el botón verde **"New"** o ve a https://github.com/new
2. Pon nombre: `nova-ai-android`
3. Marca **"Public"** (es necesario para usar Actions gratis)
4. Pulsa **"Create repository"**

### Paso 3: Subir los archivos
**Opción A — Desde el navegador (más fácil):**
1. En el repo recién creado, pulsa **"uploading an existing file"**
2. **Arrastra TODA la carpeta `android-nova`** (con todos los archivos dentro)
3. Espera a que se suban
4. Abajo pulsa **"Commit changes"**

**Opción B — Con Git desde tu PC:**
```bash
cd "android-nova"
git init
git add .
git commit -m "primer commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/nova-ai-android.git
git push -u origin main
```

### Paso 4: Esperar a que se compile
1. En tu repo, pulsa la pestaña **"Actions"**
2. Verás "🏗️ Build NOVA AI APK" corriendo (con un círculo amarillo girando)
3. **Tarda unos 20-40 minutos la primera vez** (descarga el SDK Android)
4. Cuando termine, aparece un ✅ verde

### Paso 5: Descargar la APK
1. Pulsa sobre el commit que se compiló (el que tiene ✅)
2. Baja hasta **"Artifacts"** abajo del todo
3. Pulsa **"NovaAI-APK"** → se descarga un ZIP
4. **Descomprime el ZIP** → dentro está tu `.apk` 🎉

### Paso 6: Instalar la APK en tu móvil
1. **Pasa la APK al móvil** (WhatsApp, email, Drive, USB...)
2. En el móvil, ve a **Ajustes → Seguridad → Fuentes desconocidas** (o en Android 12+: **Apps y notificaciones → Especial → Instalar apps desconocidas → permite a tu explorador**)
3. Abre el explorador de archivos en el móvil → busca el `.apk`
4. **Tócalo → Instalar**
5. Si dice "Aplicación sin verificar" → **Instalar de todas formas**
6. ¡Listo! 🌟 Busca "NOVA AI" en tu cajón de apps

---

## 🥈 OPCIÓN 2 — Linux/WSL en tu PC

Si tienes Linux o quieres usar WSL en Windows (es más rápido que GitHub Actions).

### Windows (instalar WSL):
1. Abre **CMD como administrador**
2. Ejecuta: `wsl --install -d Ubuntu`
3. Reinicia el PC
4. Crea usuario en Ubuntu cuando arranque

### Compilar:
```bash
# 1. Instalar dependencias (una sola vez)
sudo apt update
sudo apt install -y python3 python3-pip git zip unzip openjdk-17-jdk \
    autoconf libtool pkg-config zlib1g-dev libffi-dev libssl-dev \
    build-essential ccache cmake

# 2. Instalar Buildozer
pip install --user buildozer cython==0.29.36
export PATH="$HOME/.local/bin:$PATH"

# 3. Compilar (tarda 30-60 min la primera vez)
cd "android-nova"
bash compilar_apk.sh
```

La APK aparece en `bin/novaai-1.0-...debug.apk`

---

## 🥉 OPCIÓN 3 — Si solo quieres PROBAR la UI

Si solo quieres ver cómo se ve la app sin compilar nada:
- Doble clic en **`probar_en_pc.bat`** (en Windows)
- Se abre la app en tu PC y puedes navegar la interfaz
- Las acciones Android se simulan con `[sim]` (no funcionan de verdad)

---

## ❓ FAQ rápido

| Pregunta | Respuesta |
|---|---|
| ¿Puedo subir la APK directamente a la Play Store? | Sí, pero antes hay que compilar `buildozer android release` y firmarla. La debug solo sirve para uso personal. |
| ¿Por qué tan complicado? | Android requiere compilar nativo. No es como una web app. Pero la primera vez es lo más duro. |
| ¿Cuánto pesa la APK final? | ~30-40 MB |
| ¿Funciona offline? | Solo si usas Ollama (la API necesita internet) |
| ¿Es seguro instalar APKs así? | Solo si confías en el código. Esta APK la creas tú con tu propio código → 100% seguro |

---

## 🆘 Si algo falla en GitHub Actions

1. Pulsa el commit fallido en la pestaña Actions
2. Pulsa "Build NOVA AI APK"
3. Pulsa **"Compilar APK"** → verás los logs
4. Busca la línea con `ERROR` o `failed`
5. Lo más común:
   - **"License not accepted"** → vuelve a lanzar la acción (workflow_dispatch)
   - **"OutOfMemory"** → vuelve a lanzar
   - **"Buildozer not found"** → revisa que esté el archivo `.github/workflows/build-apk.yml`
