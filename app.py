import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import os

st.set_page_config(
    page_title="El Gran Teatro Mecatrónico",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Magic Theme Styling
# ---------------------------------------------------------
magic_styles = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&display=swap');

[data-testid="collapsedControl"], section[data-testid="stSidebar"], #MainMenu, footer {
    display: none !important;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Fredoka', cursive, sans-serif !important;
    background: radial-gradient(ellipse at bottom, #13092b 0%, #080314 100%) !important;
    color: #f1f5f9;
}

.star-container {
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}
.star {
    position: absolute;
    width: 3px; height: 3px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 0 8px #a855f7;
    animation: twinkle 4s infinite ease-in-out;
}
@keyframes twinkle {
    0%, 100% { opacity: 0.15; transform: scale(0.8); }
    50% { opacity: 0.95; transform: scale(1.4); }
}

.title-glow {
    text-align: center;
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #ff76ac, #a855f7, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 16px rgba(168,85,247,0.4));
    margin-bottom: 2px;
}
.subtitle {
    text-align: center;
    color: #cbd5e1;
    font-size: 1.05rem;
    margin-bottom: 20px;
}
</style>

<div class="star-container">
  <div class="star" style="top:10%; left:15%; animation-delay:0s;"></div>
  <div class="star" style="top:25%; left:80%; animation-delay:1.2s;"></div>
  <div class="star" style="top:45%; left:20%; animation-delay:2.1s;"></div>
  <div class="star" style="top:70%; left:70%; animation-delay:0.7s;"></div>
  <div class="star" style="top:85%; left:30%; animation-delay:1.8s;"></div>
</div>
"""
st.markdown(magic_styles, unsafe_allow_html=True)

# ---------------------------------------------------------
# Live Configuration
# ---------------------------------------------------------
LIVE_WOKWI_URL = "https://wokwi.com/projects/479816492813091841?embed=1"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "air_draw_story/stage_cue"

api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", None))

st.markdown('<div class="title-glow">🎭 El Gran Teatro Mecatrónico 🌟</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">¡Dibuja en el aire y mira cómo los motores físicos del escenario cobran vida en tiempo real!</div>', unsafe_allow_html=True)

if not api_key:
    with st.expander("🔑 Llave Mágica (OpenAI API Key)", expanded=True):
        temp_key = st.text_input("Ingresa tu OpenAI API Key", type="password", placeholder="sk-...")
        if temp_key:
            api_key = temp_key

component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

if "last_processed" not in st.session_state:
    st.session_state.last_processed = None
if "story_data" not in st.session_state:
    st.session_state.story_data = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "drawing_cutout" not in st.session_state:
    st.session_state.drawing_cutout = None

# Top Section: Drawing and Animated Story Box
col_draw, col_stage = st.columns([1.0, 1.0], gap="large")

with col_draw:
    st.markdown("### 🎨 Tu Lienzo en el Aire")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")

if canvas_output and api_key:
    try:
        data = json.loads(canvas_output)
        cutout_img = data.get("cutout")
        vision_img = data.get("vision")

        if cutout_img != st.session_state.last_processed:
            st.session_state.last_processed = cutout_img
            st.session_state.drawing_cutout = cutout_img

            with st.spinner("🎪 ¡El Director de Escena está coreografiando los motores!..."):
                client = OpenAI(api_key=api_key)
                base64_data = vision_img.split(",")[1]

                prompt = """
                Eres el Director Artístico de un Teatro Mecatrónico de Títeres para niños.
                Analiza el dibujo:
                1. Identifica qué dibujó el niño.
                2. Escribe un microcuento alegre e inmersivo en ESPAÑOL (máximo 3 oraciones).
                3. Define la dirección física de escena para Wokwi:
                   - mood: "FUEGO", "OCEANO", "BOSQUE", "ESPACIO" o "MAGIA".
                   - sky_r, sky_g, sky_b: Color del cielo (NeoPixel Ring).
                   - gnd_r, gnd_g, gnd_b: Color de las candilejas (NeoPixel Strip).
                   - prop_height: Altura del elevador físico (40 a 160). Si vuela/salta usa 150, si camina/nada usa 65.
                   - headline: Texto de máximo 10 caracteres para la pantalla OLED.
                4. Define 4 keyframes de baile para el recorte (x [-50 a 50], y [-25 a 25], scale [0.9 a 1.2], rotate [-15 a 15]).

                Responde ÚNICAMENTE en JSON:
                {
                  "interpretation": "descripción breve",
                  "title": "Título Cuento",
                  "story_spanish": "Había una vez...",
                  "stage_cue": {
                    "headline": "DRAGON",
                    "mood": "FUEGO",
                    "sky_r": 255, "sky_g": 60, "sky_b": 0,
                    "gnd_r": 255, "gnd_g": 180, "gnd_b": 0,
                    "prop_height": 150
                  },
                  "keyframes": [
                    { "x": 0, "y": -20, "scale": 1.15, "rotate": 8 },
                    { "x": 40, "y": -10, "scale": 0.95, "rotate": -10 },
                    { "x": -35, "y": 15, "scale": 1.1, "rotate": 12 },
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

                # Audio narration
                tts = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=story_json["story_spanish"]
                )
                st.session_state.audio_bytes = tts.content

                # Retained MQTT message ensures Wokwi catches it even if booting
                try:
                    publish.single(
                        MQTT_TOPIC,
                        json.dumps(story_json["stage_cue"]),
                        hostname=MQTT_BROKER,
                        retain=True,
                        keepalive=10
                    )
                except Exception as mqtt_err:
                    st.warning(f"MQTT: {mqtt_err}")
    except Exception as e:
        st.error(f"Aviso del teatro: {e}")

with col_stage:
    st.markdown("### 🎭 El Personaje y su Cuento")

    if st.session_state.story_data and st.session_state.drawing_cutout:
        story = st.session_state.story_data
        st.markdown(f"#### ✨ {story.get('title')}")
        st.caption(f"🌟 Criatura identificada: **{story.get('interpretation')}**")

        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3", autoplay=True)

        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.06); padding: 14px 18px; border-radius: 14px; border-left: 4px solid #a855f7; font-size: 1.05rem; line-height: 1.5; margin-bottom: 12px;">
            {story.get('story_spanish')}
            </div>
            """,
            unsafe_allow_html=True
        )

        kf = story.get("keyframes", [])
        anim_css = f"""
        @keyframes stickerDance {{
          0%   {{ transform: translate(0px, 0px) scale(1) rotate(0deg); }}
          25%  {{ transform: translate({kf[0]['x']}px, {kf[0]['y']}px) scale({kf[0]['scale']}) rotate({kf[0]['rotate']}deg); }}
          50%  {{ transform: translate({kf[1]['x']}px, {kf[1]['y']}px) scale({kf[1]['scale']}) rotate({kf[1]['rotate']}deg); }}
          75%  {{ transform: translate({kf[2]['x']}px, {kf[2]['y']}px) scale({kf[2]['scale']}) rotate({kf[2]['rotate']}deg); }}
          100% {{ transform: translate({kf[3]['x']}px, {kf[3]['y']}px) scale({kf[3]['scale']}) rotate({kf[3]['rotate']}deg); }}
        }}
        .mini-stage {{
          width: 100%;
          height: 200px;
          border-radius: 16px;
          background: radial-gradient(circle at center, #2e1065 0%, #0d061c 100%);
          border: 2px dashed rgba(168, 85, 247, 0.4);
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }}
        .dancing-cutout {{
          max-height: 150px;
          max-width: 150px;
          object-fit: contain;
          animation: stickerDance 5s infinite alternate ease-in-out;
          filter: drop-shadow(0 0 16px #38bdf8);
        }}
        """
        stage_html = f"""
        <style>{anim_css}</style>
        <div class="mini-stage">
          <img src="{st.session_state.drawing_cutout}" class="dancing-cutout"/>
        </div>
        """
        components.html(stage_html, height=215)
    else:
        st.markdown(
            """
            <div style="background: rgba(30, 20, 60, 0.4); border: 2px dashed rgba(168, 85, 247, 0.3); border-radius: 18px; height: 380px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 25px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🧚✨</div>
                <div style="font-size: 1.25rem; font-weight: 600; color: #e2e8f0;">El teatro está esperando tu creación</div>
                <div style="font-size: 0.95rem; color: #94a3b8; max-width: 300px; margin-top: 8px;">
                    1. Enciende la varita a la izquierda.<br>
                    2. Junta tus dedos para pintar.<br>
                    3. Pulsa <b>¡Darle Vida!</b> para activar los motores.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# Direct Live Wokwi Stage Embed
# ---------------------------------------------------------
st.markdown("---")
col_title, col_link = st.columns([0.8, 0.2])
with col_title:
    st.markdown("### 🎪 Escenario Físico en Vivo (Wokwi Cloud ID: `479816492813091841`)")
    st.caption("🟢 Conectado por MQTT retenido. Presiona el botón verde ▶️ en el simulador si está detenido.")
with col_link:
    st.link_button("↗️ Abrir en Wokwi", "https://wokwi.com/projects/479816492813091841")

# Single direct top-level embed with full hardware permissions
components.iframe(LIVE_WOKWI_URL, height=600, scrolling=True)
