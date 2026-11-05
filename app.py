import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
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

/* Twinkling Stardust Background Overlay */
.stars-overlay {
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
    background-image: 
        radial-gradient(1px 1px at 20px 30px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(1.5px 1.5px at 120px 80px, #38bdf8, rgba(0,0,0,0)),
        radial-gradient(1px 1px at 240px 180px, #c084fc, rgba(0,0,0,0)),
        radial-gradient(2px 2px at 380px 240px, #fde047, rgba(0,0,0,0)),
        radial-gradient(1px 1px at 540px 120px, #ffffff, rgba(0,0,0,0));
    background-repeat: repeat;
    background-size: 600px 600px;
    opacity: 0.35;
    animation: driftStars 60s linear infinite;
}
@keyframes driftStars {
    from { transform: translateY(0); }
    to { transform: translateY(-600px); }
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
    background: linear-gradient(135deg, #fbcfe8 0%, #c084fc 40%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 20px rgba(192, 132, 252, 0.4));
}
.app-subtitle {
    font-size: 0.95rem;
    color: #cbd5e1;
    margin-top: 4px;
}

/* Glassmorphism Story Card */
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

/* Stage Framing & Persistent Overlay */
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
    top: -245px;
    pointer-events: none;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
}
@keyframes floatAura {
    0%   { transform: translateY(0px) scale(1) rotate(0deg); }
    50%  { transform: translateY(-16px) scale(1.06) rotate(4deg); }
    100% { transform: translateY(0px) scale(1) rotate(0deg); }
}
.stage-cutout {
    max-height: 155px;
    max-width: 155px;
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
  <div class="app-title">🔮 El Espejo de las Historias Vivas ✨</div>
  <div class="app-subtitle">Dibuja en el aire con tus dedos. Cada trazo crea un nuevo capítulo que continúa tu historia en el teatro mecánico.</div>
</div>
""", unsafe_allow_html=True)

# Missing Key Warning
if not st.session_state.api_key:
    temp_key = st.text_input("Ingresa tu OpenAI API Key para despertar la magia:", type="password", placeholder="sk-...")
    if temp_key:
        st.session_state.api_key = temp_key.strip()
        st.rerun()

component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

col_draw, col_stage = st.columns([1.0, 1.05], gap="large")

with col_draw:
    current_chapter_num = len(st.session_state.story_chapters) + 1
    st.markdown(f"##### 🪞 El Lienzo de Luz &bull; *Capítulo {current_chapter_num}*")
    st.caption("Pellizca el índice y el pulgar para trazar con chispas de luz.")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")

# ---------------------------------------------------------
# Sequential Storytelling Processing (Continuity Engine)
# ---------------------------------------------------------
if canvas_output:
    try:
        data = json.loads(canvas_output) if isinstance(canvas_output, str) else canvas_output
        action_id = data.get("id")

        if not st.session_state.api_key:
            st.error("Se requiere una OpenAI API Key para tejer la historia.")
        elif action_id and action_id != st.session_state.processed_id:
            st.session_state.processed_id = action_id
            cutout_img = data.get("cutout")
            st.session_state.current_cutout = cutout_img

            with st.spinner(f"✨ Tejiendo el Capítulo {current_chapter_num} y animando el escenario..."):
                client = OpenAI(api_key=st.session_state.api_key)
                base64_data = data.get("vision").split(",")[1]

                # Build narrative history for true story continuity
                history_prompt = ""
                if st.session_state.story_chapters:
                    history_prompt = "HISTORIA HASTA EL MOMENTO:\n"
                    for ch in st.session_state.story_chapters:
                        history_prompt += f"- Capítulo {ch['num']} ({ch['title']}): {ch['text']}\n"
                else:
                    history_prompt = "Este es el comienzo de una nueva aventura mágica.\n"

                prompt = f"""
                Eres un narrador de cuentos mágicos e ilustrados para niños y soñadores.
                {history_prompt}

                EL USUARIO ACABA DE DIBUJAR UN NUEVO ELEMENTO EN EL AIRE (mira la imagen adjunta).

                INSTRUCCIONES:
                1. Identifica con cariño y fantasía qué criatura, objeto o símbolo dibujó.
                2. Escribe el CAPÍTULO {current_chapter_num} de la historia en ESPAÑOL (2 a 4 oraciones).
                   IMPORTANTE: Debe ser una continuación directa y fluida de los capítulos anteriores, integrando este nuevo dibujo como el siguiente suceso o personaje de la aventura.
                3. Asigna un título poético al capítulo (máx. 25 caracteres).
                4. Control del escenario mecánico Wokwi (5 servomotores y luces):
                   - kinematics: [base, hombro, codo, muñeca, herramienta] (ángulos de 25 a 155 grados).
                   - primary_rgb: [R, G, B] color luminoso principal para el anillo de estrellas.
                   - sec_rgb: [R, G, B] color secundario para las candilejas de suelo.
                5. Compón una melodía mágica de 12 a 16 notas para el escenario:
                   array "melody" con objetos {{"f": frecuencia_hz [260 a 950], "d": duracion_ms [120 a 300]}}.

                Responde ÚNICAMENTE en JSON con esta estructura:
                {{
                  "entity": "nombre del nuevo elemento",
                  "title": "Título del Capítulo",
                  "story_spanish": "Continuación de la historia...",
                  "primary_rgb": [0, 240, 255],
                  "sec_rgb": [192, 132, 252],
                  "kinematics": [90, 55, 125, 80, 110],
                  "melody": [
                    {{"f": 392, "d": 150}},
                    {{"f": 523, "d": 180}},
                    {{"f": 659, "d": 200}},
                    {{"f": 784, "d": 320}}
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
                chapter_data = json.loads(completion.choices[0].message.content)

                # Generate Spanish audio narration for this chapter
                tts = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=chapter_data["story_spanish"]
                )
                audio_bytes = tts.content
                st.session_state.current_audio = audio_bytes

                # Save to episodic story history
                st.session_state.story_chapters.append({
                    "num": current_chapter_num,
                    "title": chapter_data.get("title", f"Capítulo {current_chapter_num}"),
                    "entity": chapter_data.get("entity", "Creación mágica"),
                    "text": chapter_data.get("story_spanish", ""),
                    "cutout": cutout_img,
                    "audio": audio_bytes
                })

                # Hardware stage payload (optimized for fast transmission)
                stage_payload = {
                    "title": chapter_data.get("title", f"Capitulo {current_chapter_num}"),
                    "rgb1": chapter_data.get("primary_rgb", [0, 240, 255]),
                    "rgb2": chapter_data.get("sec_rgb", [192, 132, 252]),
                    "angles": chapter_data.get("kinematics", [90, 55, 125, 80, 110]),
                    "melody": chapter_data.get("melody", [])
                }

                # Send to live Wokwi via MQTT
                try:
                    publish.single(
                        MQTT_TOPIC,
                        json.dumps(stage_payload),
                        hostname=MQTT_BROKER,
                        retain=True,
                        keepalive=10
                    )
                except Exception as mqtt_err:
                    st.warning(f"MQTT: {mqtt_err}")

                st.rerun()

    except Exception as err:
        st.error(f"Hechizo interrumpido: {err}")

with col_stage:
    col_st_title, col_reset = st.columns([0.7, 0.3])
    with col_st_title:
        st.markdown("##### 🎪 El Escenario en Vivo & Holograma")
    with col_reset:
        if st.session_state.story_chapters:
            if st.button("✨ Nueva Aventura"):
                st.session_state.story_chapters = []
                st.session_state.current_cutout = None
                st.session_state.current_audio = None
                st.session_state.processed_id = None
                st.rerun()

    # -------------------------------------------------------------
    # Persistent Wokwi Stage (Static URL prevents simulation reset)
    # -------------------------------------------------------------
    st.markdown('<div class="stage-box">', unsafe_allow_html=True)
    components.iframe(
        f"https://wokwi.com/projects/{WOKWI_PROJECT_ID}?view=diagram",
        height=350
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Dancing Cutout Floating Layer (Non-reloading DOM Overlay)
    # -------------------------------------------------------------
    if st.session_state.current_cutout:
        st.markdown(f"""
        <div class="hologram-overlay-container">
            <img src="{st.session_state.current_cutout}" class="stage-cutout" />
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Active Chapter Story Card
    # -------------------------------------------------------------
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
          <div style="color: #cbd5e1; font-weight: 500;">El libro de historias está abierto en blanco</div>
          <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">Dibuja el primer personaje u objeto para comenzar el Capítulo 1.</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Full Illustrated Storybook History (Chronicle)
# ---------------------------------------------------------
if len(st.session_state.story_chapters) > 1:
    st.markdown("---")
    st.markdown("### 📖 Crónica del Cuento Completo")
    st.caption("Revive los capítulos anteriores creados con cada uno de tus dibujos:")

    ch_cols = st.columns(len(st.session_state.story_chapters))
    for idx, ch in enumerate(st.session_state.story_chapters):
        with ch_cols[idx]:
            st.markdown(f"**Cap. {ch['num']}: {ch['title']}**")
            if ch.get("cutout"):
                st.image(ch["cutout"], width=90)
            st.caption(ch["text"])
