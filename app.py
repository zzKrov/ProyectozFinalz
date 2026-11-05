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
# Magic Theme Styling & Integrated Playground CSS
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
# Configuration & Secrets
# ---------------------------------------------------------
WOKWI_PROJECT_ID = "479816492813091841"
MQTT_BROKER = "broker.hivemq.com"

api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", None))

st.markdown('<div class="title-glow">🎭 El Gran Teatro Mecatrónico 🌟</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">¡Dibuja en el aire y mira cómo los telones se abren, los motores mueven el escenario y tu dibujo cobra vida!</div>', unsafe_allow_html=True)

if not api_key:
    with st.expander("🔑 Falta configurar la Llave Mágica (OpenAI API Key)", expanded=True):
        temp_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
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

col_draw, col_theater = st.columns([1.0, 1.1], gap="large")

with col_draw:
    st.markdown("### 🎨 Tu Lienzo en el Aire")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")

# Handle 1-click storytelling and theatrical cue dispatch
if canvas_output and api_key:
    try:
        data = json.loads(canvas_output)
        cutout_img = data.get("cutout")
        vision_img = data.get("vision")

        if cutout_img != st.session_state.last_processed:
            st.session_state.last_processed = cutout_img
            st.session_state.drawing_cutout = cutout_img

            with st.spinner("🎪 ¡El director de escena está preparando los motores y el cuento!..."):
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
                   - gnd_r, gnd_g, gnd_b: Color de las candilejas de suelo (NeoPixel Strip).
                   - prop_height: Altura física del elevador (de 40 a 170). Si vuela/salta usa 160; si nada/camina usa 70.
                   - headline: Texto de máximo 10 caracteres para el teleprompter OLED.
                4. Define 4 keyframes CSS transform para el dibujo recortado (x [-60 a 60], y [-30 a 30], scale [0.85 a 1.25], rotate [-20 a 20]).

                Responde estricta y únicamente en formato JSON:
                {
                  "interpretation": "descripción del personaje",
                  "title": "Título Cuento",
                  "story_spanish": "Había una vez...",
                  "stage_cue": {
                    "headline": "DRAGON",
                    "mood": "FUEGO",
                    "sky_r": 255, "sky_g": 60, "sky_b": 0,
                    "gnd_r": 255, "gnd_g": 180, "gnd_b": 0,
                    "prop_height": 160
                  },
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

                # Generate Spanish voice narration
                tts = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=story_json["story_spanish"]
                )
                st.session_state.audio_bytes = tts.content

                # Send cue to Wokwi via MQTT
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
        st.error(f"Aviso del teatro: {e}")

with col_theater:
    st.markdown("### 🎪 El Escenario Mecatrónico en Vivo")
    st.caption("▶️ *Recuerda presionar el botón verde **Play** en Wokwi para encender los motores del teatro.*")

    if st.session_state.story_data and st.session_state.drawing_cutout:
        kf = st.session_state.story_data.get("keyframes", [])
        anim_css = f"""
        @keyframes magicStageDance {{
          0%   {{ transform: translate(0px, 0px) scale(1) rotate(0deg); }}
          25%  {{ transform: translate({kf[0]['x']}px, {kf[0]['y']}px) scale({kf[0]['scale']}) rotate({kf[0]['rotate']}deg); }}
          50%  {{ transform: translate({kf[1]['x']}px, {kf[1]['y']}px) scale({kf[1]['scale']}) rotate({kf[1]['rotate']}deg); }}
          75%  {{ transform: translate({kf[2]['x']}px, {kf[2]['y']}px) scale({kf[2]['scale']}) rotate({kf[2]['rotate']}deg); }}
          100% {{ transform: translate({kf[3]['x']}px, {kf[3]['y']}px) scale({kf[3]['scale']}) rotate({kf[3]['rotate']}deg); }}
        }}
        .dancing-cutout {{
          max-height: 180px;
          max-width: 180px;
          object-fit: contain;
          animation: magicStageDance 6s infinite alternate ease-in-out;
          filter: drop-shadow(0 0 20px rgba(56, 189, 248, 0.95)) drop-shadow(0 0 10px rgba(168, 85, 247, 0.8));
        }}
        """
        cutout_img_html = f'<img src="{st.session_state.drawing_cutout}" class="dancing-cutout" />'
    else:
        anim_css = ""
        cutout_img_html = """
        <div style="background: rgba(19, 9, 43, 0.75); padding: 12px 20px; border-radius: 20px; border: 1px solid rgba(168,85,247,0.4); color: #cbd5e1; font-family: sans-serif; font-size: 13px;">
          ✨ Dibuja a la izquierda y pulsa <b>¡Darle Vida!</b> para abrir los telones.
        </div>
        """

    wokwi_diagram_url = f"https://wokwi.com/projects/{WOKWI_PROJECT_ID}?view=diagram"

    unified_stage_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        {anim_css}
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
        .stage-container {{
          position: relative;
          width: 100%;
          height: 520px;
          border-radius: 20px;
          overflow: hidden;
          background: #14161f;
          border: 2px solid rgba(168, 85, 247, 0.4);
          box-shadow: 0 10px 30px rgba(112, 0, 255, 0.25);
        }}
        .wokwi-diagram {{
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 100%;
          border: none;
          z-index: 1;
        }}
        .hologram-stage {{
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 100%;
          z-index: 10;
          pointer-events: none;
          display: flex;
          align-items: center;
          justify-content: center;
        }}
      </style>
    </head>
    <body>
      <div class="stage-container">
        <iframe src="{wokwi_diagram_url}" class="wokwi-diagram"></iframe>
        <div class="hologram-stage">
          {cutout_img_html}
        </div>
      </div>
    </body>
    </html>
    """
    components.html(unified_stage_html, height=535)

    if st.session_state.story_data:
        story = st.session_state.story_data
        st.markdown(f"#### 📖 {story.get('title')}")
        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3", autoplay=True)

        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.06); padding: 12px 18px; border-radius: 12px; border-left: 4px solid #a855f7; font-size: 1.05rem; line-height: 1.5; margin-top: 6px;">
            {story.get('story_spanish')}
            </div>
            """, 
            unsafe_allow_html=True
        )
