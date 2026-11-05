import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import time
import os

st.set_page_config(
    page_title="Historias en el aire",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Warm, Understated Styling
# ---------------------------------------------------------
custom_theme = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Lora:ital,wght@0,500;1,400&display=swap');

[data-testid="collapsedControl"], section[data-testid="stSidebar"], #MainMenu, footer {
    display: none !important;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: #141312 !important;
    color: #ede6de !important;
}

.header-container {
    padding: 12px 0 20px 0;
    border-bottom: 1px solid #292623;
    margin-bottom: 24px;
}
.app-title {
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #ede6de;
}
.app-subtitle {
    font-size: 0.95rem;
    color: #9c9389;
    margin-top: 4px;
}

.story-box {
    background: #1d1b19;
    border: 1px solid #2e2b27;
    border-radius: 12px;
    padding: 16px 20px;
    margin-top: 14px;
}
.story-text {
    font-family: 'Lora', Georgia, serif;
    font-size: 1.05rem;
    line-height: 1.6;
    color: #d6cdc4;
    margin-top: 8px;
}
.story-title {
    font-weight: 600;
    font-size: 1.15rem;
    color: #ede6de;
}

div.stButton > button {
    background-color: #262320 !important;
    color: #ede6de !important;
    border: 1px solid #3d3934 !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    font-size: 0.85rem !important;
}
div.stButton > button:hover {
    background-color: #332f2a !important;
    border-color: #544e47 !important;
}
</style>
"""
st.markdown(custom_theme, unsafe_allow_html=True)

# ---------------------------------------------------------
# State & Configuration
# ---------------------------------------------------------
WOKWI_PROJECT_ID = "479816492813091841"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "air_draw_story/stage_cue"

if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
if "processed_id" not in st.session_state:
    st.session_state.processed_id = None
if "story_data" not in st.session_state:
    st.session_state.story_data = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "drawing_cutout" not in st.session_state:
    st.session_state.drawing_cutout = None
if "stage_version" not in st.session_state:
    st.session_state.stage_version = int(time.time())

# Top Header
st.markdown("""
<div class="header-container">
  <div class="app-title">Historias en el aire</div>
  <div class="app-subtitle">Dibuja una silueta frente a la cámara y mira cómo cobra vida en el escenario.</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.api_key:
    key_val = st.text_input("OpenAI API Key:", type="password", placeholder="sk-...")
    if key_val:
        st.session_state.api_key = key_val.strip()
        st.rerun()

component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

col_draw, col_stage = st.columns([1.0, 1.0], gap="large")

with col_draw:
    st.caption("Pellizca el pulgar y el índice para trazar tu figura.")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")

# Handle Drawing Submission
if canvas_output:
    try:
        data = json.loads(canvas_output) if isinstance(canvas_output, str) else canvas_output
        action_id = data.get("id")

        if not st.session_state.api_key:
            st.error("Ingresa una OpenAI API Key para crear la historia.")
        elif action_id and action_id != st.session_state.processed_id:
            st.session_state.processed_id = action_id
            st.session_state.drawing_cutout = data.get("cutout")

            with st.spinner("Creando la historia y animando el escenario..."):
                client = OpenAI(api_key=st.session_state.api_key)
                base64_data = data.get("vision").split(",")[1]

                prompt = """
                Analiza este dibujo hecho a mano en el aire:
                1. Identifica qué figura u objeto es.
                2. Escribe una historia breve, cálida y bonita en ESPAÑOL (2 o 3 oraciones).
                3. Diseña el movimiento de los 5 servos del escenario físico:
                   - kinematics: [base, hombro, codo, muñeca, herramienta] (ángulos de 25 a 155 grados).
                   - primary_rgb: [R, G, B] color cálido para las luces principales.
                   - sec_rgb: [R, G, B] color secundario de fondo.
                4. Compón una pequeña melodía agradable de 12 a 16 notas para el zumbador del escenario:
                   array "melody" con objetos {"f": frecuencia_hz [260 a 950], "d": duracion_ms [120 a 300]}.
                5. 4 keyframes suaves de animación CSS transform (x en [-45, 45], y en [-20, 20], scale [0.95, 1.15], rotate [-12, 12]).

                Responde ÚNICAMENTE en JSON con esta estructura:
                {
                  "model": "Nombre del personaje",
                  "title": "Título corto",
                  "story_spanish": "Cuento en español...",
                  "primary_rgb": [220, 120, 60],
                  "sec_rgb": [60, 130, 200],
                  "kinematics": [90, 50, 130, 90, 110],
                  "melody": [
                    {"f": 392, "d": 150},
                    {"f": 440, "d": 150},
                    {"f": 523, "d": 180},
                    {"f": 659, "d": 260},
                    {"f": 587, "d": 150},
                    {"f": 523, "d": 300}
                  ],
                  "keyframes": [
                    { "x": 0, "y": -18, "scale": 1.1, "rotate": 6 },
                    { "x": 30, "y": -8, "scale": 0.95, "rotate": -6 },
                    { "x": -25, "y": 12, "scale": 1.05, "rotate": 8 },
                    { "x": 0, "y": 0, "scale": 1.0, "rotate": 0 }
                  ]
                }
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
                story_json = json.loads(completion.choices[0].message.content)
                st.session_state.story_data = story_json

                # Audio synthesis
                tts = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=story_json["story_spanish"]
                )
                st.session_state.audio_bytes = tts.content

                # Send cue to Wokwi via MQTT
                try:
                    publish.single(
                        MQTT_TOPIC,
                        json.dumps(story_json),
                        hostname=MQTT_BROKER,
                        retain=True,
                        keepalive=10
                    )
                except Exception as e:
                    pass

                st.rerun()

    except Exception as err:
        st.error(f"Nota: {err}")

with col_stage:
    col_t, col_btn = st.columns([0.75, 0.25])
    with col_t:
        st.caption("El escenario en vivo (Wokwi)")
    with col_btn:
        if st.button("🔄 Recargar"):
            st.session_state.stage_version = int(time.time())
            st.rerun()

    # The Unified Stage Box: Live Wokwi background + Floating Cutout in foreground
    wokwi_embed_url = f"https://wokwi.com/projects/{WOKWI_PROJECT_ID}?view=diagram&v={st.session_state.stage_version}"

    if st.session_state.story_data and st.session_state.drawing_cutout:
        kf = st.session_state.story_data.get("keyframes", [])
        anim_css = f"""
        @keyframes floatDance {{
          0%   {{ transform: translate(0px, 0px) scale(1) rotate(0deg); }}
          25%  {{ transform: translate({kf[0]['x']}px, {kf[0]['y']}px) scale({kf[0]['scale']}) rotate({kf[0]['rotate']}deg); }}
          50%  {{ transform: translate({kf[1]['x']}px, {kf[1]['y']}px) scale({kf[1]['scale']}) rotate({kf[1]['rotate']}deg); }}
          75%  {{ transform: translate({kf[2]['x']}px, {kf[2]['y']}px) scale({kf[2]['scale']}) rotate({kf[2]['rotate']}deg); }}
          100% {{ transform: translate({kf[3]['x']}px, {kf[3]['y']}px) scale({kf[3]['scale']}) rotate({kf[3]['rotate']}deg); }}
        }}
        """
        overlay_html = f"""
        <img src="{st.session_state.drawing_cutout}" 
             style="max-height: 150px; max-width: 150px; object-fit: contain; animation: floatDance 5s infinite alternate ease-in-out; filter: drop-shadow(0 4px 18px rgba(0,0,0,0.85));" />
        """
    else:
        anim_css = ""
        overlay_html = """
        <div style="background: rgba(22, 21, 20, 0.75); backdrop-filter: blur(4px); padding: 8px 16px; border-radius: 20px; font-size: 13px; color: #a89f94; border: 1px solid rgba(255,255,255,0.06);">
          El escenario está listo. Dibuja algo y pulsa "Dar vida".
        </div>
        """

    stage_container_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        {anim_css}
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
        .stage-wrapper {{
          position: relative;
          width: 100%;
          height: 380px;
          border-radius: 12px;
          overflow: hidden;
          background: #181716;
          border: 1px solid #2e2b27;
          box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }}
        .wokwi-frame {{
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 100%;
          border: none;
          z-index: 1;
        }}
        .drawing-overlay {{
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 100%;
          z-index: 2;
          pointer-events: none;
          display: flex;
          align-items: center;
          justify-content: center;
        }}
      </style>
    </head>
    <body>
      <div class="stage-wrapper">
        <iframe src="{wokwi_embed_url}" class="wokwi-frame"></iframe>
        <div class="drawing-overlay">
          {overlay_html}
        </div>
      </div>
    </body>
    </html>
    """
    components.html(stage_container_html, height=395)

    # Narrative Display
    if st.session_state.story_data:
        story = st.session_state.story_data
        
        st.markdown(f"""
        <div class="story-box">
          <div class="story-title">{story.get('title', 'Historia')}</div>
          <div class="story-text">{story.get('story_spanish', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3", autoplay=True)
