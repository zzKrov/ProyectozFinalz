import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import time
import threading
import os

st.set_page_config(
    page_title="El Espejo de las Historias Vivas",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Magical & Luminous Styling
# ---------------------------------------------------------
magical_theme = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,500&display=swap');

[data-testid="collapsedControl"], section[data-testid="stSidebar"], #MainMenu, footer {
    display: none !important;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: radial-gradient(ellipse at 50% 0%, #171138 0%, #0a081a 60%, #05040d 100%) !important;
    color: #f1f5f9 !important;
}

.stars-overlay {
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
    opacity: 0.4;
    animation: driftStars 70s linear infinite;
}
@keyframes driftStars {
    from { transform: translateY(0); }
    to { transform: translateY(-550px); }
}

.header-glow {
    text-align: center;
    padding: 10px 0 16px 0;
    margin-bottom: 20px;
    border-bottom: 1px solid rgba(192, 132, 252, 0.2);
}
.app-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.3rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    background: linear-gradient(135deg, #fbcfe8 0%, #c084fc 45%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 20px rgba(192, 132, 252, 0.45));
}
.app-subtitle {
    font-size: 0.95rem;
    color: #cbd5e1;
    margin-top: 4px;
}

.story-card {
    background: rgba(26, 20, 56, 0.65);
    border: 1px solid rgba(192, 132, 252, 0.3);
    box-shadow: 0 8px 32px 0 rgba(112, 0, 255, 0.25);
    backdrop-filter: blur(14px);
    border-radius: 16px;
    padding: 16px 20px;
    margin-top: 10px;
}
.story-heading {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 4px;
}
.chapter-badge {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
    margin-bottom: 6px;
}
.story-body {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    line-height: 1.6;
    color: #e2e8f0;
}

.stage-box {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(192, 132, 252, 0.35);
    box-shadow: 0 0 30px rgba(112, 0, 255, 0.2);
    background: #0d0a1f;
}
.hologram-overlay-container {
    position: relative;
    height: 0px;
    top: -240px;
    pointer-events: none;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
}
@keyframes floatAura {
    0%   { transform: translateY(0px) scale(1) rotate(0deg); }
    50%  { transform: translateY(-14px) scale(1.06) rotate(3deg); }
    100% { transform: translateY(0px) scale(1) rotate(0deg); }
}
.stage-cutout {
    max-height: 150px;
    max-width: 150px;
    object-fit: contain;
    animation: floatAura 6s infinite ease-in-out;
    filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.95)) drop-shadow(0 0 35px rgba(192, 132, 252, 0.7));
}
</style>
<div class="stars-overlay"></div>
"""
st.markdown(magical_theme, unsafe_allow_html=True)

# ---------------------------------------------------------
# State & Configuration
# ---------------------------------------------------------
WOKWI_PROJECT_ID = "479816492813091841"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "air_draw_story/stage_cue"

def dispatch_mqtt_async(payload_dict):
    def _worker():
        try:
            publish.single(
                MQTT_TOPIC,
                json.dumps(payload_dict),
                hostname=MQTT_BROKER,
                retain=True,
                keepalive=5
            )
        except Exception as e:
            print(f"[MQTT Notice]: {e}")
    threading.Thread(target=_worker, daemon=True).start()

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

# Top Title
st.markdown("""
<div class="header-glow">
  <div class="app-title">🎭 El Pequeño Teatro de las Historias Vivas ✨</div>
  <div class="app-subtitle">Dibuja una figura en el aire. Con cada trazo, los telones se abren, la música suena y tu cuento continúa.</div>
</div>
""", unsafe_allow_html=True)

# API Key Bar (shows only if empty)
if not st.session_state.api_key:
    key_input = st.text_input("🔑 OpenAI API Key Requerida:", type="password", placeholder="sk-...")
    if key_input:
        st.session_state.api_key = key_input.strip()
        st.rerun()

component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

col_draw, col_stage = st.columns([1.0, 1.05], gap="large")

with col_draw:
    current_chapter_num = len(st.session_state.story_chapters) + 1
    st.markdown(f"##### 🪞 El Espejo de Luz &bull; *Capítulo {current_chapter_num}*")
    st.caption("Pellizca el índice y el pulgar para pintar con polvo de estrellas.")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")

# ---------------------------------------------------------
# Sequential Storytelling Processing (Continuity Engine)
# ---------------------------------------------------------
if canvas_output:
    try:
        data = json.loads(canvas_output) if isinstance(canvas_output, str) else canvas_output
        action_id = data.get("id")

        if not st.session_state.api_key:
            st.error("⚠️ Falta la OpenAI API Key. Ingrésala arriba para continuar.")
        elif action_id and action_id != st.session_state.processed_id:
            cutout_img = data.get("cutout")
            vision_raw = data.get("vision", "")
            base64_data = vision_raw.split(",")[1] if "," in vision_raw else vision_raw

            with st.spinner(f"✨ Creando el Capítulo {current_chapter_num} y componiendo la melodía..."):
                client = OpenAI(api_key=st.session_state.api_key)

                history_prompt = ""
                if st.session_state.story_chapters:
                    history_prompt = "HISTORIA HASTA EL MOMENTO:\n"
                    for ch in st.session_state.story_chapters:
                        history_prompt += f"- Capítulo {ch['num']} ({ch['title']}): {ch['text']}\n"
                else:
                    history_prompt = "Este es el comienzo de una nueva aventura mágica.\n"

                prompt = f"""
                Eres el Director Artístico y Compositor Musical de un Teatro de Marionetas para niños.
                {history_prompt}

                EL USUARIO ACABA DE DIBUJAR UN NUEVO ELEMENTO EN EL AIRE (mira la imagen adjunta).

                INSTRUCCIONES:
                1. Identifica qué criatura u objeto dibujó.
                2. Escribe el CAPÍTULO {current_chapter_num} de la historia en ESPAÑOL (2 a 3 oraciones). Continuación directa y natural de los capítulos anteriores.
                3. Asigna un título poético al capítulo (máx. 25 letras).
                4. Colores y elevador para el escenario:
                   - sky_rgb: [R, G, B] color del cielo/arco superior.
                   - foot_rgb: [R, G, B] color de las candilejas de suelo.
                   - intensity: brillo de 60 a 95.
                   - prop: altura del atrezo (40 para rastreros, 90 para caminantes, 140 para voladores).
                5. COMPOSICIÓN MUSICAL REAL (Cajita de música mágica):
                   Compón un motivo musical armónico, dulce y reconocible de 8 a 12 notas.
                   REGLA ESTRICTA DE ARMONÍA: Usa únicamente frecuencias estándar de la escala pentatónica para que suene como una melodía real y nunca como ruido:
                   C4=262, D4=294, E4=330, G4=392, A4=440, C5=523, D5=587, E5=659, G5=784 Hz (y 0 para silencio/pausa).
                   Duraciones en ms: 150 (rápida), 250 (media), 400 (larga).

                Responde ÚNICAMENTE en JSON con esta estructura:
                {{
                  "entity": "nombre del elemento",
                  "title": "Título del Capítulo",
                  "story_spanish": "Continuación del cuento...",
                  "sky_rgb": [90, 40, 220],
                  "foot_rgb": [255, 170, 50],
                  "intensity": 85,
                  "prop": 120,
                  "melody": [
                    {{"f": 392, "d": 250}},
                    {{"f": 440, "d": 250}},
                    {{"f": 523, "d": 400}},
                    {{"f": 659, "d": 250}},
                    {{"f": 0, "d": 60}},
                    {{"f": 587, "d": 250}},
                    {{"f": 523, "d": 400}}
                  ]
                }}
                """

                completion = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_data}"}}
                        ]
                    }]
                )

                raw_json = completion.choices[0].message.content.strip()
                if raw_json.startswith("```"):
                    raw_json = raw_json.strip("`").replace("json\n", "", 1)
                chapter_data = json.loads(raw_json)

                # Voice narration
                tts = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=chapter_data["story_spanish"]
                )
                audio_bytes = tts.content

                # Register state
                st.session_state.processed_id = action_id
                st.session_state.current_cutout = cutout_img
                st.session_state.current_audio = audio_bytes

                st.session_state.story_chapters.append({
                    "num": current_chapter_num,
                    "title": chapter_data.get("title", f"Capítulo {current_chapter_num}"),
                    "entity": chapter_data.get("entity", "Creación mágica"),
                    "text": chapter_data.get("story_spanish", ""),
                    "cutout": cutout_img,
                    "audio": audio_bytes
                })

                stage_payload = {
                    "title": chapter_data.get("title", f"Capítulo {current_chapter_num}"),
                    "sky_rgb": chapter_data.get("sky_rgb", [90, 40, 220]),
                    "foot_rgb": chapter_data.get("foot_rgb", [255, 170, 50]),
                    "intensity": chapter_data.get("intensity", 85),
                    "prop": chapter_data.get("prop", 120),
                    "melody": chapter_data.get("melody", [])
                }

                dispatch_mqtt_async(stage_payload)
                st.rerun()

    except Exception as err:
        st.error(f"❌ Error al generar historia: {err}")

with col_stage:
    col_st_title, col_btns = st.columns([0.65, 0.35])
    with col_st_title:
        st.markdown("##### 🎪 El Escenario Mecatrónico en Vivo")
    with col_btns:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("🔄 Sync", help="Fuerza a recargar el escenario en Wokwi"):
                st.session_state.wokwi_session_token = int(time.time())
                st.rerun()
        with btn_c2:
            if st.session_state.story_chapters:
                if st.button("✨ Reset"):
                    st.session_state.story_chapters = []
                    st.session_state.current_cutout = None
                    st.session_state.current_audio = None
                    st.session_state.processed_id = None
                    st.rerun()

    # The Persistent Wokwi Stage
    st.markdown('<div class="stage-box">', unsafe_allow_html=True)
    components.iframe(
        f"https://wokwi.com/projects/{WOKWI_PROJECT_ID}?view=diagram&v={st.session_state.wokwi_session_token}",
        height=350
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Floating Character Layer over Wokwi Stage
    if st.session_state.current_cutout:
        st.markdown(f"""
        <div class="hologram-overlay-container">
            <img src="{st.session_state.current_cutout}" class="stage-cutout" />
        </div>
        """, unsafe_allow_html=True)

    # Active Chapter Story Card
    if st.session_state.story_chapters:
        latest = st.session_state.story_chapters[-1]
        st.markdown(f"""
        <div class="story-card">
          <div class="chapter-badge">Capítulo {latest['num']} &bull; {latest['entity']}</div>
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
          <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">Dibuja la primera criatura o paisaje para tocar las campanas y abrir el telón.</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Full Illustrated Chronicle Log
# ---------------------------------------------------------
if len(st.session_state.story_chapters) > 1:
    st.markdown("---")
    st.markdown("### 📖 Crónica del Cuento Completo")
    ch_cols = st.columns(min(len(st.session_state.story_chapters), 5))
    for idx, ch in enumerate(st.session_state.story_chapters):
        col_idx = idx % 5
        with ch_cols[col_idx]:
            st.markdown(f"**Cap. {ch['num']}: {ch['title']}**")
            if ch.get("cutout"):
                st.image(ch["cutout"], width=90)
            st.caption(ch["text"])
