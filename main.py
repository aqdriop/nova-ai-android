"""
NOVA AI Android v2 — Port a móvil con TODO
==========================================
- 💬 Chat con Gemini / Groq / OpenAI
- 🎤 Reconocimiento de voz (plyer.stt)
- 🗣️ TTS para que NOVA hable
- 📷 Cámara con Intent
- 🎨 Generación de imágenes (Pollinations)
- 🌗 Tema claro/oscuro
- 📚 Historial guardado entre sesiones
- 🔐 Permisos bajo demanda

Compilar: ver COMO_INSTALAR_EN_ANDROID.md
"""

import os
import json
import threading
import urllib.request
import urllib.parse
from datetime import datetime
from io import BytesIO

# Kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.image import AsyncImage, Image
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp

# ============================================================
# DETECCIÓN DE PLATAFORMA
# ============================================================
IS_ANDROID = platform == "android"

if IS_ANDROID:
    from android.permissions import request_permissions, check_permission, Permission
    from android.storage import primary_external_storage_path, app_storage_path
    from jnius import autoclass
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    Uri = autoclass("android.net.Uri")
else:
    Permission = type("P", (), {
        "WRITE_EXTERNAL_STORAGE": "WRITE", "READ_EXTERNAL_STORAGE": "READ",
        "CAMERA": "CAM", "RECORD_AUDIO": "MIC", "INTERNET": "NET",
        "CALL_PHONE": "CALL", "SEND_SMS": "SMS",
    })()
    def request_permissions(perms, cb=None):
        if cb: cb(perms, [True]*len(perms))
    def check_permission(p): return True

# Plyer (voz, cámara, TTS — funciona en multiples plataformas)
try:
    from plyer import tts as plyer_tts
    from plyer import stt as plyer_stt
    from plyer import camera as plyer_camera
    PLYER_OK = True
except Exception:
    PLYER_OK = False
    plyer_tts = plyer_stt = plyer_camera = None

# ============================================================
# CONFIG
# ============================================================
def app_dir():
    if IS_ANDROID:
        return app_storage_path()
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

os.makedirs(app_dir(), exist_ok=True)
os.makedirs(os.path.join(app_dir(), "chats"), exist_ok=True)
os.makedirs(os.path.join(app_dir(), "imagenes"), exist_ok=True)
CONFIG_FILE = os.path.join(app_dir(), "config.json")
CHATS_DIR = os.path.join(app_dir(), "chats")
IMG_DIR = os.path.join(app_dir(), "imagenes")

PROVEEDORES = {
    "Gemini": {
        "url_key": "https://aistudio.google.com/apikey",
        "modelos": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"],
        "endpoint_chat": None,
    },
    "Groq": {
        "url_key": "https://console.groq.com/keys",
        "modelos": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768"],
        "endpoint_chat": "https://api.groq.com/openai/v1/chat/completions",
    },
    "OpenAI": {
        "url_key": "https://platform.openai.com/api-keys",
        "modelos": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        "endpoint_chat": "https://api.openai.com/v1/chat/completions",
    },
}

# ============================================================
# TEMAS
# ============================================================
TEMAS = {
    "oscuro": {
        "bg":     (0.12, 0.12, 0.18, 1),
        "bg2":    (0.10, 0.10, 0.15, 1),
        "panel":  (0.19, 0.19, 0.27, 1),
        "accent": (0.54, 0.71, 0.98, 1),
        "purple": (0.80, 0.65, 0.97, 1),
        "ok":     (0.65, 0.89, 0.63, 1),
        "warn":   (0.98, 0.89, 0.69, 1),
        "err":    (0.95, 0.55, 0.66, 1),
        "fg":     (0.81, 0.84, 0.95, 1),
        "fg_dim": (0.65, 0.68, 0.78, 1),
    },
    "claro": {
        "bg":     (0.96, 0.96, 0.98, 1),
        "bg2":    (0.90, 0.92, 0.96, 1),
        "panel":  (1.00, 1.00, 1.00, 1),
        "accent": (0.15, 0.43, 0.85, 1),
        "purple": (0.49, 0.27, 0.71, 1),
        "ok":     (0.20, 0.65, 0.30, 1),
        "warn":   (0.85, 0.55, 0.10, 1),
        "err":    (0.85, 0.20, 0.30, 1),
        "fg":     (0.12, 0.14, 0.20, 1),
        "fg_dim": (0.40, 0.42, 0.50, 1),
    },
}

def get_colors():
    cfg = cargar_config()
    return TEMAS.get(cfg.get("tema", "oscuro"), TEMAS["oscuro"])

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_config(c):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)

# ============================================================
# HISTORIAL DE CHATS
# ============================================================
class ChatStorage:
    @staticmethod
    def list_chats():
        chats = []
        for f in os.listdir(CHATS_DIR):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(CHATS_DIR, f), "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    chats.append({
                        "id": f[:-5],
                        "titulo": data.get("titulo", "Sin título"),
                        "fecha": data.get("fecha", ""),
                    })
                except Exception:
                    pass
        chats.sort(key=lambda x: x["fecha"], reverse=True)
        return chats

    @staticmethod
    def load(chat_id):
        p = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    @staticmethod
    def save(chat_id, data):
        with open(os.path.join(CHATS_DIR, f"{chat_id}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def delete(chat_id):
        p = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if os.path.exists(p): os.remove(p)

    @staticmethod
    def new_id():
        import uuid
        return datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]

# ============================================================
# SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """Eres NOVA AI Android, asistente personal en el móvil del usuario.
NUNCA ejecutas acciones directamente: el usuario SIEMPRE las aprueba con un botón.

Cuando quieras hacer acciones, responde EXCLUSIVAMENTE con un bloque JSON:

```json
{
  "explicacion": "Texto breve de lo que harás",
  "acciones": [
    {"tipo": "crear",      "ruta": "notas/x.txt", "contenido": "texto"},
    {"tipo": "leer",       "ruta": "notas/x.txt"},
    {"tipo": "borrar",     "ruta": "notas/x.txt"},
    {"tipo": "abrir_url",  "url": "https://youtube.com"},
    {"tipo": "abrir_app",  "paquete": "com.whatsapp"},
    {"tipo": "compartir",  "texto": "Hola"},
    {"tipo": "llamar",     "numero": "+34123456789"},
    {"tipo": "marcar",     "numero": "+34123456789"},
    {"tipo": "sms",        "numero": "+34123456789", "mensaje": "Hola"},
    {"tipo": "camara"},
    {"tipo": "generar_imagen", "prompt": "a cute robot"}
  ]
}
```

Si solo conversas, responde texto normal sin JSON.
Responde en español, claro y conciso. Para nombres de paquetes Android usa los oficiales."""

# ============================================================
# CLIENTE IA
# ============================================================
class IAClient:
    def __init__(self, proveedor, modelo, api_key, historial=None):
        self.proveedor = proveedor
        self.modelo = modelo
        self.api_key = api_key
        self.historial = historial or []

    def enviar(self, mensaje):
        self.historial.append({"role": "user", "content": mensaje})
        try:
            if self.proveedor == "Gemini":
                resp = self._gemini_send()
            else:
                resp = self._openai_compat()
            self.historial.append({"role": "assistant", "content": resp})
            return resp
        except Exception:
            self.historial.pop()
            raise

    def _gemini_send(self):
        url = (f"https://generativelanguage.googleapis.com/v1beta/"
               f"models/{self.modelo}:generateContent?key={self.api_key}")
        contents = []
        for m in self.historial:
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        body = {"system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": contents}
        req = urllib.request.Request(url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _openai_compat(self):
        endpoint = PROVEEDORES[self.proveedor]["endpoint_chat"]
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + self.historial
        body = {"model": self.modelo, "messages": msgs, "temperature": 0.7}
        req = urllib.request.Request(endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def reset(self): self.historial = []

# ============================================================
# VOZ — TTS y STT
# ============================================================
class Voz:
    @staticmethod
    def hablar(texto):
        """Lee texto en voz alta (TTS)."""
        if not PLYER_OK:
            print(f"[TTS no disponible] {texto}"); return
        try:
            # Recortar a 500 chars para no saturar TTS
            plyer_tts.speak(message=texto[:500])
        except Exception as e:
            print(f"Error TTS: {e}")

    @staticmethod
    def escuchar(callback):
        """Activa STT (reconocimiento de voz). callback(texto)."""
        if not PLYER_OK:
            callback(None, "STT no disponible en esta plataforma"); return

        def hacer(ok):
            if not ok:
                callback(None, "Permiso de micrófono denegado"); return
            try:
                plyer_stt.start()
                # Esperar 5 segundos (plyer es asíncrono)
                def comprobar(dt):
                    plyer_stt.stop()
                    resultados = plyer_stt.results
                    if resultados:
                        callback(resultados[0], None)
                    else:
                        callback(None, "No se entendió nada")
                Clock.schedule_once(comprobar, 5)
            except Exception as e:
                callback(None, str(e))

        if IS_ANDROID:
            AccionesAndroid.pedir_permisos([Permission.RECORD_AUDIO], hacer)
        else:
            hacer(True)

# ============================================================
# EJECUTOR DE ACCIONES
# ============================================================
class AccionesAndroid:
    @staticmethod
    def pedir_permisos(perms, callback):
        if not IS_ANDROID:
            callback(True); return
        faltantes = [p for p in perms if not check_permission(p)]
        if not faltantes:
            callback(True); return
        def _cb(perms, results):
            callback(all(results))
        request_permissions(faltantes, _cb)

    @staticmethod
    def base_storage():
        if IS_ANDROID:
            try: return primary_external_storage_path()
            except Exception: return app_storage_path()
        return os.path.join(app_dir(), "files")

    @staticmethod
    def ejecutar(accion, callback):
        tipo = accion.get("tipo")
        try:
            if tipo == "crear":
                def hacer(ok):
                    if not ok: callback("❌ Permiso denegado"); return
                    ruta = os.path.join(AccionesAndroid.base_storage(),
                                        accion.get("ruta", "archivo.txt"))
                    os.makedirs(os.path.dirname(ruta), exist_ok=True)
                    with open(ruta, "w", encoding="utf-8") as f:
                        f.write(accion.get("contenido", ""))
                    callback(f"✅ Creado: {ruta}")
                AccionesAndroid.pedir_permisos(
                    [Permission.WRITE_EXTERNAL_STORAGE], hacer)

            elif tipo == "leer":
                def hacer(ok):
                    if not ok: callback("❌ Permiso denegado"); return
                    ruta = os.path.join(AccionesAndroid.base_storage(),
                                        accion.get("ruta", ""))
                    if os.path.exists(ruta):
                        with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                            c = f.read()
                        callback(f"📄 {ruta}:\n{c[:1000]}")
                    else:
                        callback(f"⚠️ No existe: {ruta}")
                AccionesAndroid.pedir_permisos(
                    [Permission.READ_EXTERNAL_STORAGE], hacer)

            elif tipo == "borrar":
                ruta = os.path.join(AccionesAndroid.base_storage(),
                                    accion.get("ruta", ""))
                if os.path.exists(ruta):
                    os.remove(ruta); callback(f"🗑️ Borrado: {ruta}")
                else:
                    callback(f"⚠️ No existe: {ruta}")

            elif tipo == "abrir_url":
                AccionesAndroid._intent_url(accion.get("url", ""), callback)

            elif tipo == "abrir_app":
                AccionesAndroid._abrir_paquete(accion.get("paquete", ""), callback)

            elif tipo == "compartir":
                AccionesAndroid._compartir(accion.get("texto", ""), callback)

            elif tipo == "llamar":
                def hacer(ok):
                    if not ok: callback("❌ Permiso denegado"); return
                    AccionesAndroid._llamar(accion.get("numero", ""), callback)
                if IS_ANDROID:
                    AccionesAndroid.pedir_permisos([Permission.CALL_PHONE], hacer)
                else:
                    callback(f"[sim] Llamaría a {accion.get('numero')}")

            elif tipo == "marcar":
                AccionesAndroid._marcar(accion.get("numero", ""), callback)

            elif tipo == "sms":
                AccionesAndroid._sms(accion.get("numero", ""),
                                     accion.get("mensaje", ""), callback)

            elif tipo == "camara":
                AccionesAndroid._camara(callback)

            elif tipo == "generar_imagen":
                AccionesAndroid._generar_imagen(accion.get("prompt", ""), callback)

            else:
                callback(f"❓ Acción desconocida: {tipo}")

        except Exception as e:
            callback(f"❌ Error en '{tipo}': {e}")

    @staticmethod
    def _intent_url(url, cb):
        if not IS_ANDROID: cb(f"[sim] URL: {url}"); return
        try:
            intent = Intent(Intent.ACTION_VIEW)
            intent.setData(Uri.parse(url))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            PythonActivity.mActivity.startActivity(intent)
            cb(f"🌐 URL abierta: {url}")
        except Exception as e:
            cb(f"❌ Error: {e}")

    @staticmethod
    def _abrir_paquete(paquete, cb):
        if not IS_ANDROID: cb(f"[sim] App: {paquete}"); return
        try:
            pm = PythonActivity.mActivity.getPackageManager()
            intent = pm.getLaunchIntentForPackage(paquete)
            if intent is None: cb(f"⚠️ App no encontrada: {paquete}"); return
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            PythonActivity.mActivity.startActivity(intent)
            cb(f"🚀 Abierta: {paquete}")
        except Exception as e:
            cb(f"❌ Error: {e}")

    @staticmethod
    def _compartir(texto, cb):
        if not IS_ANDROID: cb(f"[sim] Compartir: {texto}"); return
        try:
            intent = Intent(Intent.ACTION_SEND)
            intent.setType("text/plain")
            intent.putExtra(Intent.EXTRA_TEXT, texto)
            chooser = Intent.createChooser(intent, "Compartir con...")
            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            PythonActivity.mActivity.startActivity(chooser)
            cb(f"📤 Compartido")
        except Exception as e:
            cb(f"❌ Error: {e}")

    @staticmethod
    def _llamar(numero, cb):
        try:
            intent = Intent(Intent.ACTION_CALL)
            intent.setData(Uri.parse(f"tel:{numero}"))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            PythonActivity.mActivity.startActivity(intent)
            cb(f"📞 Llamando a {numero}")
        except Exception as e:
            cb(f"❌ Error: {e}")

    @staticmethod
    def _marcar(numero, cb):
        if not IS_ANDROID: cb(f"[sim] Marcador: {numero}"); return
        try:
            intent = Intent(Intent.ACTION_DIAL)
            intent.setData(Uri.parse(f"tel:{numero}"))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            PythonActivity.mActivity.startActivity(intent)
            cb(f"☎️ Marcador abierto: {numero}")
        except Exception as e:
            cb(f"❌ Error: {e}")

    @staticmethod
    def _sms(numero, mensaje, cb):
        if not IS_ANDROID: cb(f"[sim] SMS a {numero}: {mensaje}"); return
        try:
            intent = Intent(Intent.ACTION_SENDTO)
            intent.setData(Uri.parse(f"smsto:{numero}"))
            intent.putExtra("sms_body", mensaje)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            PythonActivity.mActivity.startActivity(intent)
            cb(f"💬 SMS preparado para {numero}")
        except Exception as e:
            cb(f"❌ Error: {e}")

    @staticmethod
    def _camara(cb):
        """Toma foto con la cámara."""
        def hacer(ok):
            if not ok: cb("❌ Permiso de cámara denegado"); return
            try:
                ruta = os.path.join(IMG_DIR,
                    f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                if PLYER_OK and plyer_camera:
                    plyer_camera.take_picture(filename=ruta,
                        on_complete=lambda f: cb(f"📷 Foto guardada: {f}"))
                else:
                    cb("❌ plyer.camera no disponible")
            except Exception as e:
                cb(f"❌ Error cámara: {e}")
        if IS_ANDROID:
            AccionesAndroid.pedir_permisos(
                [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE], hacer)
        else:
            hacer(True)

    @staticmethod
    def _generar_imagen(prompt, cb):
        """Genera imagen con Pollinations (gratis, sin API key)."""
        def tarea():
            try:
                slug = urllib.parse.quote(prompt)
                url = f"https://image.pollinations.ai/prompt/{slug}?width=768&height=768&nologo=true"
                ruta = os.path.join(IMG_DIR,
                    f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                urllib.request.urlretrieve(url, ruta)
                cb(f"🎨 Imagen guardada: {ruta}")
            except Exception as e:
                cb(f"❌ Error generando imagen: {e}")
        threading.Thread(target=tarea, daemon=True).start()

# ============================================================
# UI
# ============================================================
Window.clearcolor = get_colors()["bg"]

def color_bg(widget, color):
    """Pinta el fondo de un widget."""
    from kivy.graphics import Color, Rectangle
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(size=widget.size, pos=widget.pos)
    widget.bind(size=lambda i,v: setattr(rect, "size", v),
                pos=lambda i,v: setattr(rect, "pos", v))
    return rect

# ============================================================
# PANTALLA: CHAT
# ============================================================
class ChatScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.cliente = None
        self.pensando = False
        self.chat_id = None
        self.colors = get_colors()
        self._build()
        Clock.schedule_once(lambda dt: self._init_cliente(), 0.5)

    def _build(self):
        C = self.colors
        root = BoxLayout(orientation="vertical")

        # ===== Topbar =====
        top = BoxLayout(size_hint_y=None, height=dp(56),
                        padding=[dp(12), dp(8)], spacing=dp(6))
        color_bg(top, C["bg2"])

        titulo = Label(
            text="[b]🌟 NOVA AI[/b]\n[size=10sp][color=8888aa]Android[/color][/size]",
            markup=True, halign="left", valign="middle",
            color=C["accent"], font_size="17sp")
        titulo.bind(size=lambda i,v: setattr(i, "text_size", v))
        top.add_widget(titulo)

        for txt, cmd, col in [
            ("📚", lambda *a: self.app.switch_to_chats(), C["panel"]),
            ("🎨", lambda *a: self.app.switch_to_imagen(), C["purple"]),
            ("⚙", lambda *a: self.app.switch_to_config(), C["panel"]),
            ("✚", lambda *a: self._nuevo_chat(), C["accent"]),
        ]:
            b = Button(text=txt, size_hint_x=None, width=dp(44),
                       background_normal="", background_color=col,
                       color=(0,0,0,1) if col == C["accent"] or col == C["purple"] else C["fg"],
                       font_size="18sp")
            b.bind(on_release=cmd)
            top.add_widget(b)
        root.add_widget(top)

        # Estado
        self.lbl_estado = Label(text="", size_hint_y=None, height=dp(22),
                                color=C["fg_dim"], font_size="11sp")
        root.add_widget(self.lbl_estado)

        # Mensajes
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self.msgs_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                  padding=[dp(10), dp(8)], spacing=dp(8))
        self.msgs_box.bind(minimum_height=self.msgs_box.setter("height"))
        self.scroll.add_widget(self.msgs_box)
        root.add_widget(self.scroll)

        # Entrada
        ef = BoxLayout(size_hint_y=None, height=dp(64),
                       padding=[dp(8), dp(8)], spacing=dp(6))
        self.entrada = TextInput(hint_text="Escribe a NOVA...",
                                 multiline=False, font_size="15sp",
                                 background_color=C["panel"],
                                 foreground_color=C["fg"],
                                 cursor_color=C["accent"],
                                 padding=[dp(12), dp(14)])
        self.entrada.bind(on_text_validate=lambda *a: self._enviar())
        ef.add_widget(self.entrada)

        b_mic = Button(text="🎤", size_hint_x=None, width=dp(50),
                       background_normal="", background_color=C["purple"],
                       color=(0,0,0,1), font_size="20sp")
        b_mic.bind(on_release=lambda *a: self._micro())
        ef.add_widget(b_mic)

        b_send = Button(text="➤", size_hint_x=None, width=dp(54),
                        background_normal="", background_color=C["accent"],
                        color=(0,0,0,1), font_size="22sp", bold=True)
        b_send.bind(on_release=lambda *a: self._enviar())
        ef.add_widget(b_send)
        root.add_widget(ef)

        self.add_widget(root)

        # Crear chat nuevo al inicio
        self._nuevo_chat(silent=True)
        self._mensaje("NOVA",
            "👋 ¡Hola! Soy NOVA AI Android.\n\n"
            "💬 Escríbeme o pulsa 🎤 para hablarme.\n"
            "📚 Ve a chats guardados con el botón de arriba.\n"
            "🎨 Pulsa el botón rosa para generar imágenes.\n\n"
            "Configura tu API Key en ⚙ si aún no lo has hecho.", "nova")

    def _init_cliente(self):
        cfg = cargar_config()
        prov = cfg.get("proveedor", "Gemini")
        modelo = cfg.get("modelo", PROVEEDORES[prov]["modelos"][0])
        api_key = cfg.get("api_keys", {}).get(prov, "")
        if not api_key:
            self.lbl_estado.text = "⚠️  Configura tu API Key en ⚙"
            self.lbl_estado.color = self.colors["warn"]
            return
        self.cliente = IAClient(prov, modelo, api_key)
        self.lbl_estado.text = f"● {prov} · {modelo}"
        self.lbl_estado.color = self.colors["ok"]

    def _nuevo_chat(self, silent=False):
        self._guardar_actual()
        self.chat_id = ChatStorage.new_id()
        self.msgs_box.clear_widgets()
        if self.cliente: self.cliente.reset()
        if not silent:
            self._mensaje("NOVA", "✨ Chat nuevo. ¿En qué te ayudo?", "nova")

    def _guardar_actual(self):
        if not self.chat_id or not self.cliente or not self.cliente.historial:
            return
        titulo = "Sin título"
        for m in self.cliente.historial:
            if m["role"] == "user":
                titulo = m["content"][:50]; break
        ChatStorage.save(self.chat_id, {
            "titulo": titulo,
            "fecha": datetime.now().isoformat(),
            "mensajes": self.cliente.historial,
        })

    def cargar_chat(self, chat_id):
        data = ChatStorage.load(chat_id)
        if not data or not self.cliente: return
        self._guardar_actual()
        self.chat_id = chat_id
        self.cliente.historial = data.get("mensajes", [])
        self.msgs_box.clear_widgets()
        for m in self.cliente.historial:
            autor = "Tú" if m["role"] == "user" else "NOVA"
            tag = "user" if m["role"] == "user" else "nova"
            self._mensaje(autor, m["content"], tag)

    def _mensaje(self, autor, texto, tipo="nova"):
        C = self.colors
        col_autor = {"user": C["accent"], "nova": C["purple"],
                     "sys": C["warn"], "err": C["err"]}.get(tipo, C["purple"])
        cont = BoxLayout(orientation="vertical", size_hint_y=None,
                         padding=[dp(12), dp(10)], spacing=dp(4))
        from kivy.graphics import Color, RoundedRectangle
        with cont.canvas.before:
            Color(*C["panel"])
            bg = RoundedRectangle(radius=[dp(12)], pos=cont.pos, size=cont.size)
        cont.bind(size=lambda i,v: setattr(bg, "size", v),
                  pos=lambda i,v: setattr(bg, "pos", v))
        la = Label(text=f"[b]{autor}[/b]", markup=True, color=col_autor,
                   font_size="13sp", size_hint_y=None, height=dp(20),
                   halign="left", valign="middle")
        la.bind(size=lambda i,v: setattr(i, "text_size", v))
        cont.add_widget(la)
        lt = Label(text=texto, color=C["fg"], font_size="14sp",
                   size_hint_y=None, halign="left", valign="top")
        lt.bind(width=lambda i,v: setattr(i, "text_size", (v, None)))
        lt.bind(texture_size=lambda i,v: setattr(i, "height", v[1]))
        cont.add_widget(lt)
        cont.bind(minimum_height=cont.setter("height"))
        self.msgs_box.add_widget(cont)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.05)

    def _enviar(self):
        texto = self.entrada.text.strip()
        if not texto or self.pensando: return
        if not self.cliente:
            self._mensaje("Error", "⚠️ Configura tu API Key primero.", "err"); return
        self.entrada.text = ""
        self._mensaje("Tú", texto, "user")
        self.pensando = True
        self._mensaje("NOVA", "🧠 Pensando...", "sys")
        threading.Thread(target=self._responder, args=(texto,), daemon=True).start()

    def _responder(self, texto):
        try:
            resp = self.cliente.enviar(texto)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._quitar_pensando(), 0)
            Clock.schedule_once(lambda dt: self._mensaje("Error",
                f"❌ {str(e)[:200]}", "err"), 0.1)
            self.pensando = False
            return
        Clock.schedule_once(lambda dt: self._procesar(resp), 0)

    def _quitar_pensando(self):
        if self.msgs_box.children:
            self.msgs_box.remove_widget(self.msgs_box.children[0])

    def _procesar(self, respuesta):
        self._quitar_pensando()
        self.pensando = False
        self._guardar_actual()  # Auto-guardar

        if "```json" in respuesta:
            try:
                i = respuesta.index("```json") + 7
                f = respuesta.index("```", i)
                data = json.loads(respuesta[i:f].strip())
                self._mensaje("NOVA", data.get("explicacion", ""), "nova")
                if cargar_config().get("voz_off", False) == False:
                    Voz.hablar(data.get("explicacion", ""))
                self._popup_permiso(data.get("acciones", []))
                return
            except Exception:
                pass

        self._mensaje("NOVA", respuesta, "nova")
        if cargar_config().get("voz_off", False) == False:
            Voz.hablar(respuesta)

    def _popup_permiso(self, acciones):
        if not acciones: return
        C = self.colors
        cont = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        sv = ScrollView()
        items = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        items.bind(minimum_height=items.setter("height"))
        for i, a in enumerate(acciones, 1):
            obj = (a.get("ruta") or a.get("url") or a.get("paquete")
                   or a.get("numero") or a.get("prompt")
                   or a.get("texto", ""))[:60]
            l = Label(text=f"{i}. [b][{a.get('tipo','?').upper()}][/b]  {obj}",
                      markup=True, color=C["fg"], size_hint_y=None, height=dp(40),
                      halign="left", valign="middle", font_size="13sp")
            l.bind(size=lambda i,v: setattr(i, "text_size", v))
            items.add_widget(l)
        sv.add_widget(items)
        cont.add_widget(sv)
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        popup = Popup(title="🔐 ¿Permitir estas acciones?", content=cont,
                      size_hint=(0.92, 0.7), separator_color=C["warn"])
        def aprobar(*a):
            popup.dismiss()
            for ac in acciones:
                AccionesAndroid.ejecutar(ac, lambda r: Clock.schedule_once(
                    lambda dt: self._mensaje("Sistema", r, "sys"), 0))
        def rechazar(*a):
            popup.dismiss()
            self._mensaje("Sistema", "❌ Acciones rechazadas.", "sys")
        b1 = Button(text="✅ Permitir", background_normal="",
                    background_color=C["ok"], color=(0,0,0,1), bold=True)
        b1.bind(on_release=aprobar)
        b2 = Button(text="❌ Rechazar", background_normal="",
                    background_color=C["err"], color=(1,1,1,1), bold=True)
        b2.bind(on_release=rechazar)
        btns.add_widget(b2); btns.add_widget(b1)
        cont.add_widget(btns)
        popup.open()

    def _micro(self):
        self._mensaje("Sistema", "🎤 Escuchando 5 segundos...", "sys")
        def resultado(texto, err):
            if err:
                Clock.schedule_once(lambda dt: self._mensaje(
                    "Error", f"🎤 {err}", "err"), 0)
            elif texto:
                Clock.schedule_once(lambda dt: setattr(self.entrada, "text", texto), 0)
                Clock.schedule_once(lambda dt: self._enviar(), 0.3)
        Voz.escuchar(resultado)

# ============================================================
# PANTALLA: HISTORIAL DE CHATS
# ============================================================
class ChatsScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.colors = get_colors()
        self._build()

    def on_enter(self):
        self._refrescar()

    def _build(self):
        C = self.colors
        root = BoxLayout(orientation="vertical")
        top = BoxLayout(size_hint_y=None, height=dp(56),
                        padding=[dp(12), dp(8)], spacing=dp(8))
        color_bg(top, C["bg2"])
        b_back = Button(text="←", size_hint_x=None, width=dp(56),
                        background_normal="", background_color=C["panel"],
                        color=C["fg"], font_size="20sp")
        b_back.bind(on_release=lambda *a: self.app.switch_to_chat())
        top.add_widget(b_back)
        top.add_widget(Label(text="[b]📚 Mis Chats[/b]", markup=True,
                             color=C["accent"], font_size="17sp"))
        root.add_widget(top)

        self.scroll = ScrollView()
        self.box = BoxLayout(orientation="vertical", size_hint_y=None,
                             padding=dp(10), spacing=dp(6))
        self.box.bind(minimum_height=self.box.setter("height"))
        self.scroll.add_widget(self.box)
        root.add_widget(self.scroll)
        self.add_widget(root)

    def _refrescar(self):
        C = self.colors
        self.box.clear_widgets()
        chats = ChatStorage.list_chats()
        if not chats:
            self.box.add_widget(Label(text="(Aún no hay chats guardados)",
                color=C["fg_dim"], size_hint_y=None, height=dp(50),
                font_size="13sp", italic=True))
            return
        for c in chats:
            row = BoxLayout(size_hint_y=None, height=dp(70),
                            padding=[dp(10), dp(6)], spacing=dp(8))
            color_bg(row, C["panel"])
            info = BoxLayout(orientation="vertical")
            t = Label(text=f"[b]{c['titulo'][:50]}[/b]", markup=True,
                      color=C["fg"], halign="left", valign="middle",
                      font_size="13sp", size_hint_y=0.6)
            t.bind(size=lambda i,v: setattr(i, "text_size", v))
            f = Label(text=c['fecha'][:16].replace("T", " "),
                      color=C["fg_dim"], halign="left", font_size="10sp",
                      size_hint_y=0.4)
            f.bind(size=lambda i,v: setattr(i, "text_size", v))
            info.add_widget(t); info.add_widget(f)
            row.add_widget(info)

            def abrir(_, cid=c["id"]):
                self.app.chat_screen.cargar_chat(cid)
                self.app.switch_to_chat()
            def borrar(_, cid=c["id"]):
                ChatStorage.delete(cid); self._refrescar()

            b1 = Button(text="📂", size_hint_x=None, width=dp(40),
                        background_normal="", background_color=C["accent"],
                        color=(0,0,0,1))
            b1.bind(on_release=abrir)
            b2 = Button(text="🗑", size_hint_x=None, width=dp(40),
                        background_normal="", background_color=C["err"],
                        color=(1,1,1,1))
            b2.bind(on_release=borrar)
            row.add_widget(b1); row.add_widget(b2)
            self.box.add_widget(row)

# ============================================================
# PANTALLA: GENERAR IMAGEN
# ============================================================
class ImagenScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.colors = get_colors()
        self._build()

    def _build(self):
        C = self.colors
        root = BoxLayout(orientation="vertical")

        top = BoxLayout(size_hint_y=None, height=dp(56),
                        padding=[dp(12), dp(8)], spacing=dp(8))
        color_bg(top, C["bg2"])
        b = Button(text="←", size_hint_x=None, width=dp(56),
                   background_normal="", background_color=C["panel"],
                   color=C["fg"], font_size="20sp")
        b.bind(on_release=lambda *a: self.app.switch_to_chat())
        top.add_widget(b)
        top.add_widget(Label(text="[b]🎨 Generar Imagen[/b]", markup=True,
                             color=C["purple"], font_size="17sp"))
        root.add_widget(top)

        body = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        body.add_widget(Label(text="Describe la imagen (mejor en inglés):",
            color=C["fg"], size_hint_y=None, height=dp(24),
            halign="left", font_size="13sp"))

        self.ti_prompt = TextInput(
            text="A cute robot painting a sunset, digital art",
            multiline=True, font_size="14sp", size_hint_y=None, height=dp(100),
            background_color=C["panel"], foreground_color=C["fg"],
            cursor_color=C["purple"], padding=[dp(12), dp(10)])
        body.add_widget(self.ti_prompt)

        self.btn_gen = Button(text="🎨  Generar con Pollinations (gratis)",
            size_hint_y=None, height=dp(52),
            background_normal="", background_color=C["purple"],
            color=(0,0,0,1), font_size="14sp", bold=True)
        self.btn_gen.bind(on_release=self._generar)
        body.add_widget(self.btn_gen)

        self.lbl_estado = Label(text="", color=C["warn"],
            size_hint_y=None, height=dp(30), font_size="12sp")
        body.add_widget(self.lbl_estado)

        # Imagen preview
        self.img_widget = AsyncImage(allow_stretch=True, keep_ratio=True)
        body.add_widget(self.img_widget)

        root.add_widget(body)
        self.add_widget(root)

    def _generar(self, *a):
        prompt = self.ti_prompt.text.strip()
        if not prompt: return
        self.lbl_estado.text = "⏳ Generando, espera unos segundos..."
        self.btn_gen.disabled = True
        def tarea():
            slug = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{slug}?width=768&height=768&nologo=true"
            ruta = os.path.join(IMG_DIR,
                f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            try:
                urllib.request.urlretrieve(url, ruta)
                Clock.schedule_once(lambda dt: self._mostrar(ruta), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(
                    self.lbl_estado, "text", f"❌ Error: {e}"), 0)
                Clock.schedule_once(lambda dt: setattr(
                    self.btn_gen, "disabled", False), 0)
        threading.Thread(target=tarea, daemon=True).start()

    def _mostrar(self, ruta):
        self.lbl_estado.text = f"✅ Guardada: {os.path.basename(ruta)}"
        self.img_widget.source = ruta
        self.img_widget.reload()
        self.btn_gen.disabled = False

# ============================================================
# PANTALLA: CONFIG
# ============================================================
class ConfigScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.colors = get_colors()
        self._build()

    def _build(self):
        C = self.colors
        root = BoxLayout(orientation="vertical")
        top = BoxLayout(size_hint_y=None, height=dp(56),
                        padding=[dp(12), dp(8)], spacing=dp(8))
        color_bg(top, C["bg2"])
        b = Button(text="← Volver", size_hint_x=None, width=dp(100),
                   background_normal="", background_color=C["panel"], color=C["fg"])
        b.bind(on_release=lambda *a: self.app.switch_to_chat())
        top.add_widget(b)
        top.add_widget(Label(text="[b]⚙ Configuración[/b]", markup=True,
                             color=C["accent"], font_size="17sp"))
        root.add_widget(top)

        sv = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None,
                        padding=dp(16), spacing=dp(12))
        box.bind(minimum_height=box.setter("height"))
        cfg = cargar_config()

        # Proveedor
        box.add_widget(self._t("Proveedor de IA"))
        prov_act = cfg.get("proveedor", "Gemini")
        self.sp_prov = Spinner(text=prov_act, values=list(PROVEEDORES.keys()),
            size_hint_y=None, height=dp(48),
            background_color=C["panel"], color=C["fg"])
        self.sp_prov.bind(text=self._cambio_prov)
        box.add_widget(self.sp_prov)

        # Modelo
        box.add_widget(self._t("Modelo"))
        mod_act = cfg.get("modelo", PROVEEDORES[prov_act]["modelos"][0])
        self.sp_mod = Spinner(text=mod_act,
            values=PROVEEDORES[prov_act]["modelos"],
            size_hint_y=None, height=dp(48),
            background_color=C["panel"], color=C["fg"])
        box.add_widget(self.sp_mod)

        # API Key
        box.add_widget(self._t("API Key"))
        self.ti_key = TextInput(text=cfg.get("api_keys", {}).get(prov_act, ""),
            password=True, multiline=False, size_hint_y=None, height=dp(48),
            background_color=C["panel"], foreground_color=C["fg"],
            cursor_color=C["accent"], padding=[dp(12), dp(14)])
        box.add_widget(self.ti_key)

        b_url = Button(text="🌐  Obtener API Key gratis",
            size_hint_y=None, height=dp(44),
            background_normal="", background_color=C["purple"], color=(0,0,0,1))
        b_url.bind(on_release=self._abrir_url)
        box.add_widget(b_url)

        # === TEMA ===
        box.add_widget(self._t("🌗 Tema visual"))
        tema_act = cfg.get("tema", "oscuro")
        self.sp_tema = Spinner(text=tema_act, values=["oscuro", "claro"],
            size_hint_y=None, height=dp(48),
            background_color=C["panel"], color=C["fg"])
        box.add_widget(self.sp_tema)

        # === VOZ ===
        box.add_widget(self._t("🔊 Voz (TTS)"))
        voz_off = cfg.get("voz_off", False)
        self.btn_voz = Button(
            text="🔇 Voz: DESACTIVADA" if voz_off else "🔊 Voz: ACTIVADA",
            size_hint_y=None, height=dp(48),
            background_normal="",
            background_color=C["err"] if voz_off else C["ok"],
            color=(0,0,0,1) if not voz_off else (1,1,1,1), bold=True)
        self.btn_voz.bind(on_release=self._toggle_voz)
        box.add_widget(self.btn_voz)

        b_test = Button(text="🔊 Probar voz", size_hint_y=None, height=dp(44),
            background_normal="", background_color=C["purple"], color=(0,0,0,1))
        b_test.bind(on_release=lambda *a:
            Voz.hablar("Hola, soy NOVA AI. Esta es mi voz."))
        box.add_widget(b_test)

        # === PERMISOS ===
        box.add_widget(self._t("📋 Permisos Android"))
        info = Label(text="NOVA pide permisos cuando los necesita.\n"
                          "Puedes solicitar los básicos ahora:",
            color=C["fg_dim"], font_size="12sp",
            size_hint_y=None, height=dp(40), halign="left")
        info.bind(size=lambda i,v: setattr(i, "text_size", v))
        box.add_widget(info)
        b_p = Button(text="📋 Solicitar permisos básicos",
            size_hint_y=None, height=dp(44),
            background_normal="", background_color=C["accent"], color=(0,0,0,1))
        b_p.bind(on_release=self._pedir_basicos)
        box.add_widget(b_p)

        # Guardar
        box.add_widget(Label(size_hint_y=None, height=dp(20)))
        b_save = Button(text="💾  Guardar configuración",
            size_hint_y=None, height=dp(56),
            background_normal="", background_color=C["ok"], color=(0,0,0,1),
            font_size="16sp", bold=True)
        b_save.bind(on_release=self._guardar)
        box.add_widget(b_save)

        sv.add_widget(box)
        root.add_widget(sv)
        self.add_widget(root)

    def _t(self, t):
        C = self.colors
        l = Label(text=f"[b]{t}[/b]", markup=True, color=C["warn"],
                  size_hint_y=None, height=dp(28),
                  halign="left", valign="middle", font_size="14sp")
        l.bind(size=lambda i,v: setattr(i, "text_size", v))
        return l

    def _cambio_prov(self, sp, value):
        mods = PROVEEDORES[value]["modelos"]
        self.sp_mod.values = mods
        self.sp_mod.text = mods[0]
        cfg = cargar_config()
        self.ti_key.text = cfg.get("api_keys", {}).get(value, "")

    def _abrir_url(self, *a):
        AccionesAndroid._intent_url(
            PROVEEDORES[self.sp_prov.text]["url_key"], lambda r: None)

    def _toggle_voz(self, *a):
        cfg = cargar_config()
        cfg["voz_off"] = not cfg.get("voz_off", False)
        guardar_config(cfg)
        C = self.colors
        if cfg["voz_off"]:
            self.btn_voz.text = "🔇 Voz: DESACTIVADA"
            self.btn_voz.background_color = C["err"]
            self.btn_voz.color = (1,1,1,1)
        else:
            self.btn_voz.text = "🔊 Voz: ACTIVADA"
            self.btn_voz.background_color = C["ok"]
            self.btn_voz.color = (0,0,0,1)

    def _pedir_basicos(self, *a):
        if not IS_ANDROID:
            self._popup("Solo Android", "Los permisos solo se piden en Android.")
            return
        perms = [Permission.WRITE_EXTERNAL_STORAGE,
                 Permission.READ_EXTERNAL_STORAGE,
                 Permission.INTERNET, Permission.RECORD_AUDIO,
                 Permission.CAMERA]
        AccionesAndroid.pedir_permisos(perms, lambda ok: self._popup(
            "Permisos", "✅ Permisos OK" if ok else "❌ Algunos denegados"))

    def _guardar(self, *a):
        cfg = cargar_config()
        prov = self.sp_prov.text
        cfg["proveedor"] = prov
        cfg["modelo"] = self.sp_mod.text
        cfg.setdefault("api_keys", {})[prov] = self.ti_key.text.strip()
        tema_nuevo = self.sp_tema.text
        tema_cambio = cfg.get("tema") != tema_nuevo
        cfg["tema"] = tema_nuevo
        guardar_config(cfg)
        self.app.chat_screen._init_cliente()
        if tema_cambio:
            self._popup("Tema",
                "✅ Tema guardado. Cierra y vuelve a abrir la app para verlo.")
        else:
            self._popup("OK", "✅ Configuración guardada.")

    def _popup(self, titulo, msg):
        Popup(title=titulo, size_hint=(0.8, 0.3),
              content=Label(text=msg, color=self.colors["fg"])).open()

# ============================================================
# APP PRINCIPAL
# ============================================================
class NovaAndroidApp(App):
    def build(self):
        self.title = "NOVA AI Android"
        self.sm = ScreenManager(transition=SlideTransition(duration=0.2))
        self.chat_screen = ChatScreen(self, name="chat")
        self.chats_screen = ChatsScreen(self, name="chats")
        self.imagen_screen = ImagenScreen(self, name="imagen")
        self.config_screen = ConfigScreen(self, name="config")
        for s in [self.chat_screen, self.chats_screen,
                  self.imagen_screen, self.config_screen]:
            self.sm.add_widget(s)
        if IS_ANDROID:
            AccionesAndroid.pedir_permisos([Permission.INTERNET], lambda ok: None)
        return self.sm

    def switch_to_chat(self):
        self.sm.transition.direction = "right"; self.sm.current = "chat"
    def switch_to_chats(self):
        self.sm.transition.direction = "left"; self.sm.current = "chats"
    def switch_to_imagen(self):
        self.sm.transition.direction = "left"; self.sm.current = "imagen"
    def switch_to_config(self):
        self.sm.transition.direction = "left"; self.sm.current = "config"


if __name__ == "__main__":
    NovaAndroidApp().run()
