import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import os

st.set_page_config(
    page_title="El Espejo Mágico de Cuentos",
    page_icon="🪄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Magic Theme Styling & Particle Animation
# ---------------------------------------------------------
magic_styles = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&display=swap');

/* Hide Streamlit Sidebar & Header */
[data-testid="collapsedControl"], section[data-testid="stSidebar"], #MainMenu, footer {
    display: none !important;
}

/* Background & Typography */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Fredoka', cursive, sans-serif !important;
    background: radial-gradient(ellipse at bottom, #1b1035 0%, #0a0614 100%) !important;
    color: #f1f5f9;
}

/* Starfield / Twinkling particles overlay */
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
    background: white;
    border-radius: 50%;
    box-shadow: 0 0 6px #a855f7;
    animation: twinkle 4s infinite ease-in-out;
}
@keyframes twinkle {
    0%, 100% { opacity: 0.2; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1.4); }
}

/* Glassmorphism Cards */
.magic-card {
    background: rgba(30, 20, 60, 0.55);
    border: 1px solid rgba(168, 85, 247, 0.3);
    box-shadow: 0 8px 32px 0 rgba(112, 0, 255, 0.2);
    backdrop-filter: blur(12px);
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 20px;
}

.title-glow {
    text-align: center;
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #ff76ac, #a855f7, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 16px rgba(168,85,247,0.4));
    margin-bottom: 0px;
}
.subtitle {
    text-align: center;
    color: #cbd5e1;
    font-size: 1.1rem;
    margin-bottom: 25px;
}
</style>

<!-- Floating Stars -->
<div class="star-container">
  <div class="star" style="top:10%; left:15%; animation-delay:0s;"></div>
  <div class="star" style="top:25%; left:80%; animation-delay:1.2s;"></div>
  <div class="star" style="top:45%; left:25%; animation-delay:2.1s;"></div>
  <div class="star" style="top:70%; left:65%; animation-delay:0.7s;"></div>
  <div class="star" style="top:85%; left:35%; animation-delay:1.8s;"></div>
  <div class="star" style="top:15%; left:50%; animation-delay:2.7s;"></div>
  <div class="star" style="top:60%; left:90%; animation-delay:3.3s;"></div>
</div>
"""
st.markdown(magic_styles, unsafe_allow_html=True)

# ---------------------------------------------------------
# Secrets & Wokwi Project Setup
# ---------------------------------------------------------
WOKWI_PROJECT_ID = "479816492813091841"
MQTT_BROKER = "broker.hivemq.com"

api_key = st.secrets.get("OPENAI_API_KEY", None)

# Header
st.markdown('<div class="title-glow">🪄 El Espejo Mágico de Cuentos 🌟</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">¡Dibuja en el aire con tus dedos y mira cómo tu creación cobra vida en pantalla y en el mundo real!</div>', unsafe_allow_html=True)

if not api_key:
    st.warning("✨ Falta la llave mágica (`OPENAI_API_KEY`) en los Secretos de Streamlit para despertar la historia.")

# Load Drawing Component
component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

# Session States
if "last_processed" not in st.session_state:
    st.session_state.last_processed = None
if "story_data" not in st.session_state:
    st.session_state.story_data = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "drawing_cutout" not in st.session_state:
    st.session_state.drawing_cutout = None

# Top Screen: Stage & Canvas
col_draw, col_stage = st.columns([1.1, 0.9], gap="large")

with col_draw:
    st.markdown("### 🎨 Tu Lienzo de Polvo de Estrellas")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")

# Handle automatic one-click magic when drawing is sent
if canvas_output and api_key:
    try:
        data = json.loads(canvas_output)
        cutout_img = data.get("cutout")
        vision_img = data.get("vision")

        # Process only when a fresh drawing arrives
        if cutout_img != st.session_state.last_processed:
            st.session_state.last_processed = cutout_img
            st.session_state.drawing_cutout = cutout_img

            with st.spinner("🌟 ¡La varita mágica está tejiendo tu historia!..."):
                client = OpenAI(api_key=api_key)
                base64_data = vision_img.split(",")[1]

                prompt = """
                Eres un narrador de cuentos de hadas para niños.
                1. Identifica qué dibujó el niño en el aire.
                2. Crea un microcuento fantástico, dulce y emocionante en ESPAÑOL (máximo 3 o 4 oraciones).
                3. Genera 4 pasos de baile/movimiento (keyframes) en CSS transform:
                   (x en [-60, 60] px, y en [-30, 30] px, scale en [0.85, 1.25], rotate en [-20, 20] deg).
                4. Elige un color mágico para iluminar los faros (RGB) y un título simpático (máximo 16 caracteres).

                Responde ÚNICAMENTE en JSON:
                {
                  "interpretation": "descripción cariñosa del dibujo",
                  "title": "Título Mágico",
                  "story_spanish": "Cuento encantador...",
                  "stage_cue": { "r": 255, "g": 120, "b": 0, "headline": "Título Mágico" },
                  "keyframes": [
                    { "x": 0, "y": -25, "scale": 1.15, "rotate": 10 },
                    { "x": 50, "y": -15, "scale": 0.9, "rotate": -12 },
                    { "x": -45, "y": 20, "scale": 1.2, "rotate": 15 },
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

                # Magic Voice
                tts = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=story_json["story_spanish"]
                )
                st.session_state.audio_bytes = tts.content

                # Send cue to Wokwi animatronics via MQTT
                try:
                    publish.single(
                        "air_draw_story/stage_cue",
                        json.dumps(story_json["stage_cue"]),
                        hostname=MQTT_BROKER,
                        keepalive=5
                    )
                except Exception:
                    pass
    except Exception as e:
        st.error(f"Ocurrió un pequeño hechizo fallido: {e}")

with col_stage:
    st.markdown("### 🎭 El Escenario Encantado")

    if st.session_state.story_data and st.session_state.drawing_cutout:
        story = st.session_state.story_data
        
        st.markdown(f"#### ✨ {story.get('title')}")
        st.write(f"🌟 **Creaste:** *{story.get('interpretation')}*")
        
        # Audio Player
        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3", autoplay=True)

        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.06); padding: 14px; border-radius: 12px; border-left: 4px solid #a855f7; font-size: 1.05rem; line-height: 1.5;">
            {story.get('story_spanish')}
            </div>
            """, 
            unsafe_allow_html=True
        )

        # Dynamic Cutout Animation
        kf = story.get("keyframes", [])
        anim_css = f"""
        @keyframes magicDance {{
          0%   {{ transform: translate(0px, 0px) scale(1) rotate(0deg); }}
          25%  {{ transform: translate({kf[0]['x']}px, {kf[0]['y']}px) scale({kf[0]['scale']}) rotate({kf[0]['rotate']}deg); }}
          50%  {{ transform: translate({kf[1]['x']}px, {kf[1]['y']}px) scale({kf[1]['scale']}) rotate({kf[1]['rotate']}deg); }}
          75%  {{ transform: translate({kf[2]['x']}px, {kf[2]['y']}px) scale({kf[2]['scale']}) rotate({kf[2]['rotate']}deg); }}
          100% {{ transform: translate({kf[3]['x']}px, {kf[3]['y']}px) scale({kf[3]['scale']}) rotate({kf[3]['rotate']}deg); }}
        }}
        .stage-box {{
          width: 100%;
          height: 250px;
          background: radial-gradient(circle at center, #2e1065 0%, #0f0728 100%);
          border-radius: 18px;
          border: 2px dashed rgba(168, 85, 247, 0.4);
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          margin-top: 15px;
        }}
        .dancing-cutout {{
          max-height: 160px;
          max-width: 160px;
          object-fit: contain;
          animation: magicDance 6s infinite alternate ease-in-out;
          filter: drop-shadow(0 0 18px #38bdf8);
        }}
        """
        stage_html = f"""
        <style>{anim_css}</style>
        <div class="stage-box">
          <img src="{st.session_state.drawing_cutout}" class="dancing-cutout"/>
        </div>
        """
        components.html(stage_html, height=270)
    else:
        st.markdown(
            """
            <div style="background: rgba(30, 20, 60, 0.4); border: 2px dashed rgba(168, 85, 247, 0.3); border-radius: 18px; height: 380px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 25px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🧚✨</div>
                <div style="font-size: 1.25rem; font-weight: 600; color: #e2e8f0;">El teatro está esperando tu creación</div>
                <div style="font-size: 0.95rem; color: #94a3b8; max-width: 300px; margin-top: 8px;">
                    1. Enciende el espejo con la varita.<br>
                    2. Junta tus deditos para dibujar.<br>
                    3. Pulsa <b>¡Darle Vida!</b> para comenzar la magia.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# Bottom Screen: Embedded Live Physical Theater (Wokwi)
# ---------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🎪 El Teatro Físico Encantado (Wokwi en Vivo)")
st.caption("¡Mira cómo giran los rotores animatrónicos y brilla la corona de luces cuando cobra vida tu cuento!")

wokwi_url = f"https://wokwi.com/projects/{WOKWI_PROJECT_ID}"
components.iframe(wokwi_url, height=540, scrolling=True)
