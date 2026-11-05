import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import json
import time
import socket
import re
import base64
import threading
import os

st.set_page_config(
    page_title="El Espejo de las Historias Vivas",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Global Constants & Configuration
# ---------------------------------------------------------
WOKWI_PROJECT_ID = "479816492813091841"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "air_draw_story/stage_cue"
MQTT_TOPIC_TELEMETRY = "air_draw_story/telemetry"

# ---------------------------------------------------------
# Global Telemetry Store (Wokwi -> Streamlit)
# ---------------------------------------------------------
if "latest_telemetry" not in st.session_state:
    st.session_state.latest_telemetry = {
        "origen": "ESP32_Wokwi",
        "estado": "STANDBY",
        "telon": "CERRADO",
        "ultimo_acto": "Ninguno",
        "uptime_seg": 0,
        "hora": "-"
    }

def start_telemetry_listener():
    def _on_msg(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            payload["hora"] = time.strftime("%H:%M:%S")
            st.session_state.latest_telemetry = payload
        except Exception:
            pass

    def _worker():
        client = mqtt.Client(f"Streamlit_Monitor_{int(time.time())}")
        client.on_message = _on_msg
        try:
            client.connect(MQTT_BROKER, 1883, 10)
            client.subscribe(MQTT_TOPIC_TELEMETRY)
            client.loop_forever()
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

if "telemetry_thread_started" not in st.session_state:
    st.session_state.telemetry_thread_started = True
    start_telemetry_listener()

# ---------------------------------------------------------
# Helper to Embed Images Safely in HTML Report
# ---------------------------------------------------------
def render_report_image(filename, title, caption):
    if os.path.exists(filename):
        try:
            with open(filename, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                return f"""<div class="image-slot"><img src="data:image/png;base64,{b64}" style="width:100%;border-radius:10px;border:1px solid rgba(192,132,252,0.4);display:block;"/><div class="image-slot-caption">{caption}</div></div>"""
        except Exception:
            pass
    return f"""<div class="image-slot"><div style="font-size:1.3rem;">🖼️ <b>{filename}</b></div><div style="font-weight:600;font-size:0.85rem;color:#cbd5e1;margin-top:4px;">{title}</div><div class="image-slot-caption">{caption}</div></div>"""

slot_img_4 = render_report_image("4.png", "Trazado Gestual en el Aire", "Figura 4: Interfaz de dibujo aéreo y captura gestual mediante pinza (4.png)")
slot_img_3 = render_report_image("3.png", "Crónica de Capítulos Continuos", "Figura 3: Registro inferior de capítulos secuenciales e historia viva (3.png)")
slot_img_2 = render_report_image("2.png", "Estado Inicial en Reposo", "Figura 2: Estado inicial del circuito Wokwi — Telones cerrados y reposo (2.png)")
slot_img_1 = render_report_image("1.png", "Actuación en Vivo y Partitura", "Figura 1: Actuación en vivo — Música en zumbador, OLED activa y luces encendidas (1.png)")

# ---------------------------------------------------------
# Luminous Theme & Pure CSS Drawer
# ---------------------------------------------------------
magical_theme = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,500&display=swap');

html, body, [data-testid="stAppViewContainer"], .main, .drawer-content {{
    scroll-behavior: smooth !important;
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
    z-index: 10 !important;
}}
[data-testid="collapsedControl"], section[data-testid="stSidebar"], #MainMenu, footer {{
    display: none !important;
}}

html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: radial-gradient(ellipse at 50% 0%, #171138 0%, #0a081a 60%, #05040d 100%) !important;
    color: #f1f5f9 !important;
    overflow-x: hidden;
}}

.stars-overlay {{
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
    background-image: 
        radial-gradient(1.2px 1.2px at 30px 40px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(1.8px 1.8px at 140px 90px, #38bdf8, rgba(0,0,0,0)),
        radial-gradient(1.2px 1.2px at 280px 200px, #c084fc, rgba(0,0,0,0)),
        radial-gradient(2px 2px at 420px 280px, #fde047, rgba(0,0,0,0));
    background-repeat: repeat;
    background-size: 550px 550px;
    opacity: 0.35;
    animation: driftStars 80s linear infinite;
}}
@keyframes driftStars {{
    from {{ transform: translateY(0); }}
    to {{ transform: translateY(-550px); }}
}}

.header-glow {{
    text-align: center;
    padding: 8px 0 10px 0;
    margin-bottom: 10px;
    border-bottom: 1px solid rgba(192, 132, 252, 0.2);
}}
.app-title {{
    font-family: 'Playfair Display', serif;
    font-size: 2.1rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    background: linear-gradient(135deg, #fbcfe8 0%, #c084fc 45%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 20px rgba(192, 132, 252, 0.45));
}}
.app-subtitle {{
    font-size: 0.88rem;
    color: #cbd5e1;
    margin-top: 2px;
}}

/* Real Container Target Selectors */
div:has(> iframe[title*="air_canvas"]),
[data-testid="element-container"]:has(iframe[title*="air_canvas"]) {{
    position: relative !important;
    border-radius: 16px !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}

div:has(> iframe[src*="wokwi.com"]),
[data-testid="element-container"]:has(iframe[src*="wokwi.com"]) {{
    position: relative !important;
    border-radius: 16px !important;
    background: #0d0a1f !important;
    border: 1px solid rgba(192, 132, 252, 0.35) !important;
    box-shadow: 0 0 30px rgba(112, 0, 255, 0.2) !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}

/* Telemetry Slide Animation */
.telemetry-slide-reveal {{
    animation: slideDownFade 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
}}
@keyframes slideDownFade {{
    from {{ opacity: 0; transform: translateY(-25px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.story-card {{
    background: rgba(26, 20, 56, 0.65);
    border: 1px solid rgba(192, 132, 252, 0.3);
    box-shadow: 0 8px 32px 0 rgba(112, 0, 255, 0.22);
    backdrop-filter: blur(14px);
    border-radius: 16px;
    padding: 16px 20px;
    margin-top: 8px;
    transition: all 0.3s ease;
}}
.story-heading {{
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 4px;
}}
.chapter-badge {{
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
}}
.music-badge {{
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(192, 132, 252, 0.15);
    color: #c084fc;
    border: 1px solid rgba(192, 132, 252, 0.35);
    margin-left: 6px;
}}
.story-body {{
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    line-height: 1.65;
    color: #e2e8f0;
    margin-top: 6px;
}}

/* Floating Hologram Layer */
.hologram-overlay-container {{
    position: relative;
    height: 0px;
    top: -240px;
    pointer-events: none;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
}}
@keyframes floatAura {{
    0%   {{ transform: translateY(0px) scale(1) rotate(0deg); }}
    50%  {{ transform: translateY(-14px) scale(1.06) rotate(3deg); }}
    100% {{ transform: translateY(0px) scale(1) rotate(0deg); }}
}}
.stage-cutout {{
    max-height: 150px;
    max-width: 150px;
    object-fit: contain;
    animation: floatAura 6s infinite ease-in-out;
    filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.95)) drop-shadow(0 0 35px rgba(192, 132, 252, 0.7));
}}

div.stButton > button {{
    background: rgba(30, 27, 75, 0.7) !important;
    color: #ede6de !important;
    border: 1px solid rgba(192, 132, 252, 0.3) !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    padding: 4px 12px !important;
}}

/* Pure CSS Drawer */
.drawer-checkbox {{
    display: none !important;
}}
.drawer-trigger-btn {{
    position: fixed;
    top: 14px;
    right: 20px;
    z-index: 10000000 !important;
    background: linear-gradient(135deg, rgba(192, 132, 252, 0.35), rgba(56, 189, 248, 0.35)) !important;
    border: 1.5px solid rgba(192, 132, 252, 0.8) !important;
    backdrop-filter: blur(16px);
    color: #ffffff !important;
    padding: 8px 18px !important;
    border-radius: 30px !important;
    font-size: 0.86rem !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    box-shadow: 0 0 25px rgba(192, 132, 252, 0.6) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    display: inline-flex !important;
    align-items: center;
    gap: 8px;
    user-select: none;
}}
.drawer-trigger-btn:hover {{
    transform: translateY(-2px) scale(1.05);
    border-color: #38bdf8 !important;
    box-shadow: 0 0 35px rgba(56, 189, 248, 0.8) !important;
}}

.drawer-inline-btn {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 4px;
    background: rgba(30, 27, 75, 0.8);
    border: 1px solid rgba(192, 132, 252, 0.5);
    color: #c084fc;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    user-select: none;
}}
.drawer-inline-btn:hover {{
    color: #38bdf8;
    border-color: #38bdf8;
    background: rgba(56, 189, 248, 0.15);
}}

.drawer-panel {{
    position: fixed;
    top: 0;
    right: 0;
    width: 500px;
    max-width: 92vw;
    height: 100vh;
    background: rgba(15, 11, 33, 0.97) !important;
    backdrop-filter: blur(28px);
    border-left: 1px solid rgba(192, 132, 252, 0.4) !important;
    box-shadow: -15px 0 55px rgba(0, 0, 0, 0.85) !important;
    z-index: 10000000 !important;
    transform: translateX(105%);
    transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}}

/* Clean, transparent backdrop with zero blur to keep site razor-sharp */
.drawer-backdrop {{
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(5, 4, 13, 0.12) !important;
    backdrop-filter: none !important;
    z-index: 9999999 !important;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
}}

.drawer-checkbox:checked ~ .drawer-panel {{
    transform: translateX(0) !important;
}}
.drawer-checkbox:checked ~ .drawer-backdrop {{
    opacity: 1 !important;
    pointer-events: auto !important;
}}

.drawer-header {{
    padding: 18px 22px;
    border-bottom: 1px solid rgba(192, 132, 252, 0.25);
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.drawer-title {{
    font-family: 'Playfair Display', serif;
    font-size: 1.35rem;
    font-weight: 600;
    background: linear-gradient(135deg, #fbcfe8, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.drawer-close-label {{
    background: rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    font-size: 1.2rem;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    user-select: none;
}}
.drawer-close-label:hover {{
    color: #fff;
    background: rgba(244, 63, 94, 0.35);
}}

.drawer-content {{
    padding: 22px;
    overflow-y: auto;
    flex: 1;
    font-size: 0.92rem;
    line-height: 1.6;
    color: #e2e8f0;
}}
.drawer-content::-webkit-scrollbar {{
    width: 6px;
}}
.drawer-content::-webkit-scrollbar-thumb {{
    background: rgba(192, 132, 252, 0.25);
    border-radius: 10px;
}}

.drawer-section-title {{
    font-size: 1.05rem;
    font-weight: 700;
    color: #38bdf8;
    margin-top: 18px;
    margin-bottom: 8px;
}}

.companion-link {{
    display: inline-block;
    padding: 3px 10px;
    margin: 3px 2px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}}
.companion-link.cyan {{
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.45);
}}
.companion-link.red {{
    background: rgba(244, 63, 94, 0.15);
    color: #fb7185;
    border: 1px solid rgba(244, 63, 94, 0.45);
}}
.companion-link.gold {{
    background: rgba(251, 191, 36, 0.15);
    color: #fde047;
    border: 1px solid rgba(251, 191, 36, 0.45);
}}
.companion-link.purple {{
    background: rgba(192, 132, 252, 0.15);
    color: #c084fc;
    border: 1px solid rgba(192, 132, 252, 0.45);
}}
.companion-link:hover {{
    transform: translateX(-3px) scale(1.05);
    filter: brightness(1.2);
}}

.image-slot {{
    width: 100%;
    margin: 14px 0 16px 0;
    border: 1.5px dashed rgba(192, 132, 252, 0.35);
    border-radius: 12px;
    background: rgba(15, 12, 33, 0.5);
    padding: 12px;
    text-align: center;
    box-sizing: border-box;
}}
.image-slot-caption {{
    font-size: 0.78rem;
    color: #94a3b8;
    margin-top: 6px;
    font-style: italic;
}}
</style>

<div class="stars-overlay"></div>
<input type="checkbox" id="drawer-toggle" class="drawer-checkbox">
<label for="drawer-toggle" class="drawer-trigger-btn"><span>🟢</span><span>📋 Informe del Proyecto</span></label>
<label for="drawer-toggle" class="drawer-backdrop"></label>
<div class="drawer-panel">
<div class="drawer-header">
<div class="drawer-title">Informe & Guía Interactiva</div>
<label for="drawer-toggle" class="drawer-close-label">✕</label>
</div>
<div class="drawer-content">
<div style="font-size:0.78rem;color:#a855f7;font-weight:600;margin-bottom:12px;">ESTUDIANTE: Juan David Segura &bull; INTERFACES MULTIMODALES</div>
<div class="drawer-section-title">✨ ¿Qué es este proyecto?</div>
<p>Es un <b>teatro interactivo que mezcla lo digital con lo físico</b>. Dibujas figuras en el aire con tus dedos frente a la cámara web, y el sistema convierte ese dibujo en un cuento narrado por voz, le compone una melodía musical original y hace que un escenario físico en miniatura (simulado en Wokwi) actúe la escena abriendo telones y moviendo piezas en tiempo real.</p>
<div class="drawer-section-title">🎛️ ¿Qué es el Selector de Ambientes y la Vista Dual?</div>
<p>Para cumplir los requisitos de interfaces multimodales, el sistema cuenta con dos ambientes interactivos y un modo unificado:</p>
<ul style="padding-left:18px;margin-top:4px;">
<li style="margin-bottom:6px;"><b>Ambiente 1 (Teatro & Narrativa):</b> Modo creativo. Usa visión artificial para dibujar en el aire, genera cuentos ilustrados por capítulos con voz en alta definición y proyecta el dibujo flotante sobre el proscenio.</li>
<li style="margin-bottom:6px;"><b>Ambiente 2 (Consola & Telemetría):</b> Modo de ingeniería. Permite controlar manualmente los servomotores con barras deslizadoras (sliders), cambiar colores y monitorear la telemetría bidireccional en vivo enviada desde el ESP32.</li>
<li style="margin-bottom:6px;"><b>Vista Dual (Ambos a la vez):</b> Muestra ambos ambientes simultáneamente en la misma pantalla para ver el cuento, el escenario y los instrumentos técnicos al mismo tiempo.</li>
</ul>
<div class="drawer-section-title">⚙️ ¿Cómo funciona?</div>
<ol style="padding-left:18px;margin-top:4px;">
<li style="margin-bottom:10px;"><b>Dibujo en el aire:</b> La cámara web rastrea tu mano. Al juntar el pulgar y el índice (gesto de pinza), el sistema pinta una línea luminosa en pantalla.<br><span class="companion-link cyan" data-target="canvas" data-color="#38bdf8">🔍 Resaltar Lienzo de Dibujo</span></li>
{slot_img_4}
<li style="margin-bottom:10px;"><b>La IA interpreta y crea:</b><ul style="padding-left:16px;margin-top:4px;"><li>Reconoce la figura y escribe el siguiente capítulo del cuento (recordando los capítulos anteriores para que la historia tenga continuidad).</li><li>Narra la historia con voz en español usando entonación y pausas dramáticas (<span class="companion-link purple" data-target="story" data-color="#c084fc">tts-1-hd con voz modulada</span>).</li><li>Compone una melodía real (notas musicales afinadas y con ritmo, no ruido al azar).</li></ul></li>
{slot_img_3}
<li style="margin-bottom:10px;"><b>El escenario cobra vida:</b><ul style="padding-left:16px;margin-top:4px;"><li>En tu pantalla, tu dibujo aparece recortado flotando y bailando sobre el escenario.</li><li>Por internet (vía MQTT), la placa ESP32 en Wokwi recibe la orden: abre los telones, enciende las luces del color del cuento, eleva al personaje y toca la melodía con su zumbador como una cajita de música.</li></ul></li>
<li style="margin-bottom:10px;"><b>Telemetría de retorno bidireccional:</b> Al iniciar y finalizar cada acto, el ESP32 transmite de vuelta a Streamlit su estado físico, confirmando que la orden fue ejecutada en el circuito.<br><span class="companion-link cyan" data-target="telemetry" data-color="#38bdf8">📡 Resaltar Monitor de Telemetría</span></li>
</ol>
<div class="drawer-section-title">🦾 ¿Qué hace cada servomotor exactamente?</div>
<p>A continuación se observa el estado de reposo del teatro antes de que se inicie la obra:</p>
{slot_img_2}
<ul style="padding-left:18px;margin-top:4px;">
<li style="margin-bottom:10px;"><b>Servos 13 y 25 (Telón izquierdo y derecho):</b> Empiezan cerrados en el centro. Cuando empieza la historia se abren hacia los lados para revelar el escenario, y se vuelven a cerrar cuando termina el acto.<br><span class="companion-link red" data-target="curtains" data-color="#f43f5e">🎭 Resaltar Telones en Escenario</span></li>
<li style="margin-bottom:10px;"><b>Servo 14 (Elevador de personaje):</b> Funciona como una trampilla debajo del escenario. Sube físicamente al personaje a la escena (sube poco si es un animal terrestre y sube alto si es un ave o dragón volador), y lo baja al terminar.<br><span class="companion-link gold" data-target="prop" data-color="#fbbf24">🚀 Resaltar Elevador Mecánico</span></li>
<li style="margin-bottom:10px;"><b>Servo 27 (Máquina de viento):</b> Se balancea suavemente de un lado a otro mientras suena la música para darle movimiento escénico al fondo (simulando brisa o marea).<br><span class="companion-link cyan" data-target="wind" data-color="#38bdf8">🌪️ Resaltar Máquina de Viento</span></li>
</ul>
<div class="drawer-section-title">💡 El resto del hardware en acción:</div>
{slot_img_1}
<ul style="padding-left:18px;margin-top:4px;">
<li style="margin-bottom:6px;"><b>Luces LED (Anillo y Tira):</b> Iluminan el arco del cielo y el suelo con el color y brillo que elija la IA para la escena.</li>
<li style="margin-bottom:6px;"><b>Pantalla OLED:</b> Muestra el título de la obra y el nombre de la partitura que está sonando.</li>
<li style="margin-bottom:6px;"><b>Zumbador:</b> Toca la partitura que compuso la IA nota por nota a un volumen suave como cajita de música.</li>
</ul>
<div style="text-align:center;margin-top:25px;padding-top:15px;border-top:1px solid rgba(192,132,252,0.2);font-size:0.8rem;color:#94a3b8;">Pasa el mouse sobre los botones para auto-desplazar la página y trazar estelas luminosas.</div>
</div>
</div>
"""
st.markdown(magical_theme, unsafe_allow_html=True)

# ---------------------------------------------------------
# Synchronous MQTT Transmitter
# ---------------------------------------------------------
def send_stage_cue(payload_dict):
    prev_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(3.5)
        publish.single(
            MQTT_TOPIC,
            json.dumps(payload_dict),
            hostname=MQTT_BROKER,
            port=1883,
            retain=True,
            keepalive=5
        )
        st.toast("📡 ¡Partitura transmitida al teatro!", icon="🎼")
        return True
    except Exception as e:
        st.warning(f"Aviso de conexión con el escenario: {e}")
        return False
    finally:
        socket.setdefaulttimeout(prev_timeout)

if "wokwi_session_token" not in st.session_state:
    st.session_state.wokwi_session_token = int(time.time())
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
if "story_chapters" not in st.session_state:
    st.session_state.story_chapters = []
if "processed_id" not in st.session_state:
    st.session_state.processed_id = None
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None
if "current_cutout" not in st.session_state:
    st.session_state.current_cutout = None
if "ai_model" not in st.session_state:
    st.session_state.ai_model = "gpt-4o-mini"
if "narrator_voice" not in st.session_state:
    st.session_state.narrator_voice = "coral"

# ---------------------------------------------------------
# Header & Navigation Switcher
# ---------------------------------------------------------
st.markdown("""
<div class="header-glow">
  <div class="app-title">🎭 El Pequeño Teatro de las Historias Vivas ✨</div>
  <div class="app-subtitle">Dibuja en el aire o controla el escenario físico mediante interfaces multimodales.</div>
  <div>
    <label for="drawer-toggle" class="drawer-inline-btn">
      <span>📖</span>
      <span>Ver Informe & Guía Interactiva</span>
    </label>
  </div>
</div>
""", unsafe_allow_html=True)

view_mode = st.radio(
    "Selecciona el Ambiente Interactivo:",
    options=[
        "🎭 Ambiente 1: Teatro & Narrativa",
        "🎛️ Ambiente 2: Consola & Telemetría",
        "🪟 Vista Dual (Ambos Ambientes a la vez)"
    ],
    horizontal=True,
    index=0,
    key="nav_view_mode_radio"
)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================================
# AMBIENTE 1: TEATRO & NARRATIVA GESTUAL
# =========================================================================
def render_ambiente_1():
    with st.expander("⚙️ Ajustes del Narrador & Conexión", expanded=not bool(st.session_state.api_key)):
        cfg_col1, cfg_col2, cfg_col3 = st.columns([1.2, 1, 1])
        with cfg_col1:
            key_input = st.text_input("OpenAI API Key:", value=st.session_state.api_key, type="password", placeholder="sk-...", key="key_input_amb1")
            if key_input != st.session_state.api_key:
                st.session_state.api_key = key_input.strip()
                st.rerun()
        with cfg_col2:
            voice_opt = st.selectbox(
                "Voz del Narrador (HD):",
                options=["coral", "fable", "onyx", "nova"],
                index=["coral", "fable", "onyx", "nova"].index(st.session_state.narrator_voice),
                format_func=lambda x: {
                    "coral": "Coral (Cálida y Expresiva)",
                    "fable": "Fable (Teatral británica)",
                    "onyx": "Onyx (Profunda y Épica)",
                    "nova": "Nova (Luminosa y Vivaz)"
                }.get(x, x),
                key="voice_select_amb1"
            )
            st.session_state.narrator_voice = voice_opt
        with cfg_col3:
            model_opt = st.selectbox(
                "Motor de IA:",
                options=["gpt-4o-mini", "gpt-4o"],
                index=0 if st.session_state.ai_model == "gpt-4o-mini" else 1,
                format_func=lambda x: "Ultrarrápido (gpt-4o-mini ~1.5s)" if "mini" in x else "Alta Definición (gpt-4o)",
                key="model_select_amb1"
            )
            st.session_state.ai_model = model_opt

    component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
    air_canvas = components.declare_component("air_canvas", path=component_path)

    col_draw, col_stage = st.columns([1.0, 1.05], gap="large")

    with col_draw:
        current_chapter_num = len(st.session_state.story_chapters) + 1
        st.markdown(f"##### 🪞 El Espejo de Luz &bull; *Capítulo {current_chapter_num}*")
        st.caption("Pellizca el índice y el pulgar para pintar con polvo de estrellas.")
        canvas_output = air_canvas(default=None, key="air_canvas_ui")

    if canvas_output:
        try:
            data = json.loads(canvas_output) if isinstance(canvas_output, str) else canvas_output
            action_id = data.get("id")

            if not st.session_state.api_key:
                st.error("⚠️ Ingresa tu OpenAI API Key en los ajustes superiores para despertar la historia.")
            elif action_id and action_id != st.session_state.processed_id:
                cutout_img = data.get("cutout")
                vision_raw = data.get("vision", "")
                base64_data = vision_raw.split(",")[1] if "," in vision_raw else vision_raw

                with st.spinner(f"🎼 Componiendo partitura y tejiendo el Capítulo {current_chapter_num}..."):
                    client = OpenAI(api_key=st.session_state.api_key)

                    history_prompt = ""
                    if st.session_state.story_chapters:
                        history_prompt = "HISTORIA HASTA EL MOMENTO:\n"
                        for ch in st.session_state.story_chapters:
                            history_prompt += f"- Capítulo {ch['num']} ({ch['title']}): {ch['text']}\n"
                    else:
                        history_prompt = "Este es el comienzo de una nueva aventura mágica.\n"

                    prompt = f"""
                    Eres simultáneamente el Narrador Dramático y el Maestro Compositor Musical de un Teatro de Marionetas.
                    {history_prompt}

                    EL USUARIO ACABA DE DIBUJAR UN NUEVO ELEMENTO EN EL AIRE (mira la imagen adjunta).

                    INSTRUCCIONES DE NARRATIVA EMOCIONAL:
                    1. Identifica qué criatura u objeto dibujó el usuario.
                    2. Escribe el CAPÍTULO {current_chapter_num} de la historia en ESPAÑOL (2 a 3 oraciones ricas en expresividad). Continuación fluida de los capítulos previos.
                    3. MODULACIÓN VOCAL RICA: Usa signos de puntuación dramática (puntos suspensivos '...' para misterio, exclamaciones '¡!', guiones largos '—' para pausas solemnes, comas fluidas) para que la voz modulada exprese emoción viva, asombro y matices.
                    4. Asigna un título poético (máx. 25 letras).

                    INSTRUCCIONES DE COMPOSICIÓN MUSICAL (PARTITURA ORIGINAL):
                    5. Bautiza la pieza musical con un título evocador (ej: "Danza del Viento", "Nana de la Luna", "Marcha de las Estrellas").
                    6. Carácter emocional breve (ej: "Lírico y Soñador", "Misterioso", "Jovial").
                    7. COMPÓN UNA MELODÍA ARMÓNICA Y REAL de 8 a 14 notas musicales.
                       REGLA OBLIGATORIA DE FRECUENCIAS (Cajita de música cálida, tonos graves y medios, NUNCA chirridos agudos):
                       - Usa EXCLUSIVAMENTE notas afinadas de la escala pentatónica:
                         G3: 196 Hz | A3: 220 Hz | B3: 247 Hz | C4: 262 Hz | D4: 294 Hz | E4: 330 Hz | F4: 349 Hz | G4: 392 Hz | A4: 440 Hz | C5: 523 Hz
                         (Usa 0 para silencios y pausas rítmicas indispensables).
                       - Duraciones en ms: 180 (ligera), 280 (media), 450 (nota reposada final).
                       - Concluye la melodía reposando en la tónica (C4: 262 o G3: 196).

                    8. Parámetros del escenario mecánico:
                       - sky_rgb: [R, G, B] color del cielo/arco superior.
                       - foot_rgb: [R, G, B] color cálido de las candilejas de suelo.
                       - intensity: brillo de 65 a 90.
                       - prop: elevación del atrezo (40 para rastreros, 90 para caminantes, 140 para voladores/mágicos).

                    Responde ÚNICAMENTE en JSON con esta estructura:
                    {{
                      "entity": "nombre del elemento",
                      "title": "Título del Capítulo",
                      "story_spanish": "Cuento en español con puntuación expresiva...",
                      "score_title": "Nombre de la Canción",
                      "score_mood": "Carácter emocional",
                      "sky_rgb": [90, 40, 220],
                      "foot_rgb": [255, 170, 50],
                      "intensity": 85,
                      "prop": 120,
                      "melody": [
                        {{"f": 262, "d": 280}},
                        {{"f": 330, "d": 280}},
                        {{"f": 392, "d": 450}},
                        {{"f": 0, "d": 90}},
                        {{"f": 440, "d": 260}},
                        {{"f": 392, "d": 260}},
                        {{"f": 330, "d": 450}}
                      ]
                    }}
                    """

                    completion = client.chat.completions.create(
                        model=st.session_state.ai_model,
                        response_format={"type": "json_object"},
                        messages=[
                            {
                                "role": "system",
                                "content": "Eres un narrador de cuentos teatrales expresivo y compositor musical. Respondes exclusivamente en formato JSON válido."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}}
                                ]
                            }
                        ]
                    )

                    choice = completion.choices[0]
                    message = choice.message

                    if getattr(message, "refusal", None):
                        raise ValueError(f"El modelo no pudo procesar la figura: {message.refusal}")

                    raw_content = message.content
                    if not raw_content:
                        raise ValueError(f"Respuesta vacía del modelo (motivo: {choice.finish_reason}).")

                    match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                    clean_json = match.group(0) if match else raw_content.strip()
                    chapter_data = json.loads(clean_json)

                    # High-Fidelity Voice Synthesis
                    story_text = chapter_data.get("story_spanish", "Había una vez una figura mágica que cobró vida.")
                    tts = client.audio.speech.create(
                        model="tts-1-hd",
                        voice=st.session_state.narrator_voice,
                        input=story_text
                    )
                    audio_bytes = tts.content

                    st.session_state.processed_id = action_id
                    st.session_state.current_cutout = cutout_img
                    st.session_state.current_audio = audio_bytes

                    st.session_state.story_chapters.append({
                        "num": current_chapter_num,
                        "title": chapter_data.get("title", f"Capítulo {current_chapter_num}"),
                        "score_title": chapter_data.get("score_title", "Melodía Mágica"),
                        "score_mood": chapter_data.get("score_mood", "Encantador"),
                        "entity": chapter_data.get("entity", "Creación mágica"),
                        "text": story_text,
                        "cutout": cutout_img,
                        "audio": audio_bytes
                    })

                    stage_payload = {
                        "title": chapter_data.get("title", f"Capítulo {current_chapter_num}"),
                        "score_title": chapter_data.get("score_title", "Melodía Mágica"),
                        "sky_rgb": chapter_data.get("sky_rgb", [90, 40, 220]),
                        "foot_rgb": chapter_data.get("foot_rgb", [255, 170, 50]),
                        "intensity": chapter_data.get("intensity", 85),
                        "prop": chapter_data.get("prop", 120),
                        "melody": chapter_data.get("melody", [])
                    }

                    send_stage_cue(stage_payload)
                    st.rerun()

        except Exception as err:
            st.error(f"❌ Error al generar historia: {err}")

    with col_stage:
        col_st_title, col_btns = st.columns([0.55, 0.45])
        with col_st_title:
            st.markdown("##### 🎪 El Escenario Mecatrónico en Vivo")
        with col_btns:
            btn_c1, btn_c2, btn_c3 = st.columns(3)
            with btn_c1:
                if st.button("🔔 Probar", help="Envía una partitura de prueba a Wokwi", key="btn_probar_amb1"):
                    test_cue = {
                        "title": "Acto de Prueba",
                        "score_title": "Danza de Prueba",
                        "sky_rgb": [0, 240, 255],
                        "foot_rgb": [255, 120, 40],
                        "intensity": 90,
                        "prop": 135,
                        "melody": [
                            {"f": 262, "d": 260},
                            {"f": 330, "d": 260},
                            {"f": 392, "d": 380},
                            {"f": 0,   "d": 80},
                            {"f": 523, "d": 450}
                        ]
                    }
                    send_stage_cue(test_cue)
            with btn_c2:
                if st.button("🔄 Sync", help="Fuerza a recargar el simulador Wokwi", key="btn_sync_amb1"):
                    st.session_state.wokwi_session_token = int(time.time())
                    st.rerun()
            with btn_c3:
                if st.session_state.story_chapters:
                    if st.button("✨ Reset", key="btn_reset_amb1"):
                        st.session_state.story_chapters = []
                        st.session_state.current_cutout = None
                        st.session_state.current_audio = None
                        st.session_state.processed_id = None
                        st.rerun()

        st.caption("💡 *Asegúrate de pulsar el botón verde ▶️ (Play) dentro de Wokwi para encender el escenario.*")

        components.iframe(
            f"https://wokwi.com/projects/{WOKWI_PROJECT_ID}?view=diagram&v={st.session_state.wokwi_session_token}",
            height=350
        )

        if st.session_state.current_cutout:
            st.markdown(f"""
            <div class="hologram-overlay-container">
                <img src="{st.session_state.current_cutout}" class="stage-cutout" />
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.story_chapters:
            latest = st.session_state.story_chapters[-1]
            st.markdown(f"""
            <div class="story-card">
              <div>
                <span class="chapter-badge">Capítulo {latest['num']} &bull; {latest['entity']}</span>
                <span class="music-badge">🎼 {latest.get('score_title', 'Partitura')} ({latest.get('score_mood', 'Mágico')})</span>
              </div>
              <div class="story-heading">{latest['title']}</div>
              <div class="story-body">{latest['text']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.current_audio:
                st.audio(st.session_state.current_audio, format="audio/mp3", autoplay=True)
        else:
            st.markdown("""
            <div class="story-card" style="text-align: center; padding: 24px;">
              <div style="font-size: 2rem; margin-bottom: 6px;">✨📜</div>
              <div style="color: #cbd5e1; font-weight: 500;">El teatro está en penumbra esperando la función</div>
              <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">Dibuja la primera criatura o paisaje para abrir el telón y escuchar su música original.</div>
            </div>
            """, unsafe_allow_html=True)

    if len(st.session_state.story_chapters) > 1:
        st.markdown("---")
        st.markdown("### 📖 Crónica del Cuento Completo")
        ch_cols = st.columns(min(len(st.session_state.story_chapters), 5))
        for idx, ch in enumerate(st.session_state.story_chapters):
            col_idx = idx % 5
            with ch_cols[col_idx]:
                st.markdown(f"**Cap. {ch['num']}: {ch['title']}**")
                st.caption(f"🎼 *{ch.get('score_title', 'Canción')}*")
                if ch.get("cutout"):
                    st.image(ch["cutout"], width=90)
                st.caption(ch["text"])

# =========================================================================
# AMBIENTE 2: CONSOLA DE DIRECCIÓN & TELEMETRÍA (WOKWI -> STREAMLIT)
# =========================================================================
def render_ambiente_2():
    st.markdown("### 🎛️ Consola de Dirección y Telemetría Ciberfísica")
    st.caption("Ambiente de control técnico manual, calibración de actuadores y monitor de telemetría bidireccional.")

    col_ctrl, col_mon = st.columns([1, 1], gap="large")

    with col_ctrl:
        st.subheader("1. Mandos Manuales del Escenario")
        st.caption("Controla manualmente los servomotores y luces del circuito Wokwi:")

        tab_servos, tab_luces = st.tabs(["🦾 Calibración Servomotores", "💡 Iluminación Escénica"])

        with tab_servos:
            c1, c2 = st.columns(2)
            with c1:
                telon_izq = st.slider("Telón Izquierdo (Pin 13)", 0, 90, 0, help="0° cerrado, 90° abierto", key="slider_telon_izq_amb2")
                elevador = st.slider("Elevador de Atrezo (Pin 14)", 20, 150, 20, help="20° reposo, 140° escena", key="slider_elevador_amb2")
            with c2:
                telon_der = st.slider("Telón Derecho (Pin 25)", 90, 180, 180, help="180° cerrado, 90° abierto", key="slider_telon_der_amb2")
                viento = st.slider("Máquina de Viento (Pin 27)", 70, 110, 90, help="90° neutro", key="slider_viento_amb2")

        with tab_luces:
            c_sky = st.color_picker("Color Arco Proscenio (Cielo)", "#5A28DC", key="picker_sky_amb2")
            c_foot = st.color_picker("Color Candilejas (Piso)", "#FFA032", key="picker_foot_amb2")
            brillo = st.slider("Intensidad Luminosa (%)", 10, 100, 85, key="slider_brillo_amb2")

        if st.button("📡 Enviar Comandos Manuales a Wokwi", type="primary", key="btn_send_manual_amb2"):
            h_sky = c_sky.lstrip("#")
            rgb_sky = [int(h_sky[i:i+2], 16) for i in (0, 2, 4)]
            h_foot = c_foot.lstrip("#")
            rgb_foot = [int(h_foot[i:i+2], 16) for i in (0, 2, 4)]

            payload = {
                "title": "Mando Manual",
                "score_title": "Intervencion Manual",
                "sky_rgb": rgb_sky,
                "foot_rgb": rgb_foot,
                "intensity": brillo,
                "prop": elevador,
                "melody": [{"f": 262, "d": 200}, {"f": 330, "d": 200}, {"f": 392, "d": 350}]
            }
            send_stage_cue(payload)

    with col_mon:
        st.subheader("2. Telemetría de Retorno en Vivo (Wokwi ➔ Streamlit)")
        st.caption("Verificación del canal de comunicación bidireccional MQTT:")

        t_data = st.session_state.latest_telemetry
        st.markdown(f"""
        <div id="target-telemetry-box" style="position:relative; background: rgba(18, 14, 40, 0.8); border: 1.5px solid rgba(56, 189, 248, 0.4); border-radius: 12px; padding: 16px;">
          <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
            <span style="font-weight:700; color:#38bdf8;">📡 DISPOSITIVO: {t_data.get('origen')}</span>
            <span style="color:#94a3b8; font-size:0.85rem;">Hora: {t_data.get('hora')}</span>
          </div>
          <div style="font-size:0.95rem; line-height:1.7;">
            &bull; <b>Estado Escénico:</b> <code style="color:#c084fc;">{t_data.get('estado')}</code><br>
            &bull; <b>Posición de Telones:</b> <code style="color:#fde047;">{t_data.get('telon')}</code><br>
            &bull; <b>Último Acto Interpretado:</b> <i>{t_data.get('ultimo_acto')}</i><br>
            &bull; <b>Tiempo Activo ESP32:</b> {t_data.get('uptime_seg')} segundos
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Refrescar Monitor de Telemetría", key="btn_refresh_telemetry_amb2"):
            st.rerun()

        st.markdown("""
        ---
        ##### Canal Bidireccional
        * **Streamlit $\\rightarrow$ Wokwi:** `air_draw_story/stage_cue`
        * **Wokwi $\\rightarrow$ Streamlit:** `air_draw_story/telemetry`
        """)

# =========================================================================
# ROUTING & DUAL VIEW ENGINE
# =========================================================================
st.markdown('<div id="ambience-1-wrapper">', unsafe_allow_html=True)
if "Ambiente 1" in view_mode or "Dual" in view_mode:
    render_ambiente_1()
st.markdown('</div>', unsafe_allow_html=True)

if "Dual" in view_mode:
    st.markdown("---")

amb2_display = "block" if ("Ambiente 2" in view_mode or "Dual" in view_mode) else "none"
st.markdown(f'<div id="ambience-2-wrapper" style="display:{amb2_display};">', unsafe_allow_html=True)
render_ambiente_2()
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Companion Engine (Encoded Payload: Auto-Scroll & Particles)
# ---------------------------------------------------------
companion_js_code = """
(function() {
    var doc = document;
    if (!doc || !doc.body) return;

    var canvas = doc.getElementById('companion-trail-canvas');
    if (!canvas) {
        canvas = doc.createElement('canvas');
        canvas.id = 'companion-trail-canvas';
        canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:10000001;';
        doc.body.appendChild(canvas);
    }
    var ctx = canvas.getContext('2d');

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    var particles = [];
    var isHovering = false;
    var currentSource = null;
    var currentTarget = null;
    var currentColor = '#38bdf8';
    var animId = null;
    var tempTelemetryTimer = null;

    function getTarget(key) {
        if (key === 'canvas') {
            return doc.querySelector('div:has(> iframe[title*="air_canvas"])') ||
                   doc.querySelector('[data-testid="element-container"]:has(iframe[title*="air_canvas"])') ||
                   doc.querySelector('[data-testid="stColumn"]:first-child');
        }
        if (key === 'stage' || key === 'curtains' || key === 'prop' || key === 'wind') {
            return doc.querySelector('div:has(> iframe[src*="wokwi.com"])') ||
                   doc.querySelector('[data-testid="element-container"]:has(iframe[src*="wokwi.com"])');
        }
        if (key === 'story') {
            return doc.querySelector('.story-card');
        }
        if (key === 'telemetry') {
            return doc.getElementById('target-telemetry-box') || doc.querySelector('#ambience-2-wrapper');
        }
        return null;
    }

    function scrollToElement(el) {
        if (!el) return;
        el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
    }

    function spawnParticles() {
        if (!isHovering || !currentSource || !currentTarget) return;

        var rectA = currentSource.getBoundingClientRect();
        var rectB = currentTarget.getBoundingClientRect();

        var x0 = rectA.left;
        var y0 = rectA.top + rectA.height / 2;

        var x1 = rectB.right;
        var y1 = rectB.top + rectB.height / 2;

        var cx = (x0 + x1) / 2;
        var cy = Math.min(y0, y1) - 60;

        for (var i = 0; i < 3; i++) {
            particles.push({
                x0: x0, y0: y0, x1: x1, y1: y1,
                cx: cx, cy: cy,
                t: 0,
                speed: 0.024 + Math.random() * 0.02,
                size: 2.2 + Math.random() * 3.2,
                wobble: (Math.random() - 0.5) * 14,
                color: currentColor
            });
        }
    }

    function render() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        spawnParticles();

        if (isHovering && currentTarget) {
            var r = currentTarget.getBoundingClientRect();
            var p = 6;
            var bx = r.left - p, by = r.top - p, bw = r.width + p * 2, bh = r.height + p * 2;

            ctx.save();
            ctx.strokeStyle = currentColor;
            ctx.lineWidth = 3.5;
            ctx.shadowColor = currentColor;
            ctx.shadowBlur = 24;

            if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(bx, by, bw, bh, 14);
                ctx.stroke();
            } else {
                ctx.strokeRect(bx, by, bw, bh);
            }

            var len = 22;
            ctx.lineWidth = 5;
            ctx.beginPath();
            ctx.moveTo(bx, by + len); ctx.lineTo(bx, by); ctx.lineTo(bx + len, by);
            ctx.moveTo(bx + bw - len, by); ctx.lineTo(bx + bw, by); ctx.lineTo(bx + bw, by + len);
            ctx.moveTo(bx, by + bh - len); ctx.lineTo(bx, by + bh); ctx.lineTo(bx + len, by + bh);
            ctx.moveTo(bx + bw - len, by + bh); ctx.lineTo(bx + bw, by + bh); ctx.lineTo(bx + bw, by + bh - len);
            ctx.stroke();
            ctx.restore();
        }

        for (var j = particles.length - 1; j >= 0; j--) {
            var pt = particles[j];
            pt.t += pt.speed;
            if (pt.t >= 1) { particles.splice(j, 1); continue; }

            var invT = 1 - pt.t;
            var curX = invT * invT * pt.x0 + 2 * invT * pt.t * pt.cx + pt.t * pt.t * pt.x1;
            var curY = invT * invT * pt.y0 + 2 * invT * pt.t * pt.cy + pt.t * pt.t * pt.y1;
            curY += Math.sin(pt.t * Math.PI * 4) * pt.wobble;

            var alpha = pt.t < 0.2 ? pt.t / 0.2 : (1 - pt.t);
            ctx.save();
            ctx.beginPath();
            ctx.arc(curX, curY, pt.size * (1 - pt.t * 0.35), 0, 2 * Math.PI);
            ctx.fillStyle = pt.color;
            ctx.shadowColor = pt.color;
            ctx.shadowBlur = 12;
            ctx.globalAlpha = alpha;
            ctx.fill();
            ctx.restore();
        }

        if (particles.length > 0 || isHovering) {
            animId = requestAnimationFrame(render);
        } else {
            animId = null;
        }
    }

    function startAnimation() {
        if (!animId) animId = requestAnimationFrame(render);
    }

    function bind() {
        var links = doc.querySelectorAll('.companion-link');
        links.forEach(function(l) {
            if (l.dataset.bound) return;
            l.dataset.bound = 'true';

            l.addEventListener('mouseenter', function() {
                var targetKey = l.getAttribute('data-target');
                var color = l.getAttribute('data-color') || '#38bdf8';

                if (targetKey === 'telemetry') {
                    if (tempTelemetryTimer) clearTimeout(tempTelemetryTimer);
                    var amb2 = doc.getElementById('ambience-2-wrapper');
                    if (amb2 && (amb2.style.display === 'none' || getComputedStyle(amb2).display === 'none')) {
                        amb2.style.display = 'block';
                        amb2.classList.add('telemetry-slide-reveal');
                    }
                }

                var targetEl = getTarget(targetKey);
                if (targetEl) {
                    isHovering = true;
                    currentSource = l;
                    currentTarget = targetEl;
                    currentColor = color;

                    scrollToElement(targetEl);
                    startAnimation();
                }
            });

            l.addEventListener('mouseleave', function() {
                isHovering = false;
                currentTarget = null;
                currentSource = null;

                var targetKey = l.getAttribute('data-target');
                if (targetKey === 'telemetry') {
                    tempTelemetryTimer = setTimeout(function() {
                        var amb2 = doc.getElementById('ambience-2-wrapper');
                        var radio = doc.querySelector('[data-testid="stRadio"] input[type="radio"]:checked');
                        var radioLabel = radio ? (radio.closest('label') || {}).innerText || '' : '';
                        if (amb2 && radioLabel.indexOf('Ambiente 2') === -1 && radioLabel.indexOf('Dual') === -1) {
                            amb2.style.display = 'none';
                            amb2.classList.remove('telemetry-slide-reveal');
                        }
                    }, 1400);
                }
            });
        });
    }

    setInterval(bind, 800);
})();
"""

encoded_js = base64.b64encode(companion_js_code.encode("utf-8")).decode("ascii")
st.markdown(f"""<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" style="display:none;" onload="eval(atob('{encoded_js}'))" />""", unsafe_allow_html=True)
