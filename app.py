import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import os

st.set_page_config(
    page_title="Kinetic Automata Lab // Generative Fab-Cell",
    page_icon="🦾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Cybernetic Atelier Theme: Obsidian Titanium & Slate
# ---------------------------------------------------------
studio_theme = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@500;700&display=swap');

[data-testid="collapsedControl"], section[data-testid="stSidebar"], #MainMenu, footer {
    display: none !important;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Space Grotesk', sans-serif !important;
    background: #090a10 !important;
    color: #e2e8f0;
}

.mono {
    font-family: 'JetBrains Mono', monospace !important;
}

.hud-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(56, 189, 248, 0.2);
    padding-bottom: 14px;
    margin-bottom: 24px;
}
.brand-title {
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #38bdf8 0%, #a855f7 50%, #f43f5e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.status-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    background: rgba(56, 189, 248, 0.1);
    color: #38bdf8;
    padding: 6px 14px;
    border-radius: 9999px;
    border: 1px solid rgba(56, 189, 248, 0.3);
    letter-spacing: 1px;
}

.lab-card {
    background: #0f121d;
    border: 1px solid #1e2438;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}
</style>
"""
st.markdown(studio_theme, unsafe_allow_html=True)

# ---------------------------------------------------------
# Live Configuration
# ---------------------------------------------------------
# '?view=diagram' forces Wokwi to hide all code tabs and display pure hardware
LIVE_WOKWI_URL = "https://wokwi.com/projects/479816492813091841?view=diagram"
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "air_draw_story/stage_cue"

api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", None))

st.markdown("""
<div class="hud-header">
  <div>
    <div class="brand-title">KINETIC LAB // AUTONOMOUS AUTOMATA FAB-CELL</div>
    <div style="font-size: 0.85rem; color: #64748b; margin-top: 3px;">
      Spatial Vector Synthesis &bull; 5-Axis Robotic Kinematics &bull; Algorithmic Chiptune Synthesis
    </div>
  </div>
  <div class="status-pill">SYS_CORE: ONLINE &bull; 60 FPS</div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    with st.expander("🔑 AUTENTICACIÓN: Configurar OpenAI API Key", expanded=True):
        temp_key = st.text_input("OpenAI Secret Key", type="password", placeholder="sk-...")
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

col_draw, col_stage = st.columns([1.0, 1.0], gap="large")

with col_draw:
    st.markdown("##### 📐 TERMINAL DE DIBUJO VECTORIAL // AIRE")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")

# Generative AI Processing: Visual Recognition + Kinematics + Melody
if canvas_output and api_key:
    try:
        data = json.loads(canvas_output)
        cutout_img = data.get("cutout")
        vision_img = data.get("vision")

        if cutout_img != st.session_state.last_processed:
            st.session_state.last_processed = cutout_img
            st.session_state.drawing_cutout = cutout_img

            with st.spinner("⚡ Calculando Cinemática Inversa y Componiendo Melodía Algorítmica..."):
                client = OpenAI(api_key=api_key)
                base64_data = vision_img.split(",")[1]

                prompt = """
                Eres el Diseñador Principal de un Laboratorio de Robótica Cinemática y Compositor de Música Electrónica.
                Analiza el dibujo espacial:
                1. Clasifica el objeto o entidad con nombre de ingeniería (ej: "CYBER-DRAGON // AERO-V").
                2. Escribe una historia cautivadora y fantástica en ESPAÑOL (3 oraciones máximo).
                3. Define la cinemática de ensamblaje para un brazo robótico de 5 ejes:
                   - kinematics: [anguloBase, anguloHombro, anguloCodo, anguloMuñeca, anguloHerramienta] (de 15 a 165 grados).
                   - primary_rgb: [R, G, B] color láser principal.
                   - sec_rgb: [R, G, B] color espectral secundario.
                4. COMPÓN UNA MELODÍA ORIGINAL:
                   Genera un array "melody" de 12 a 16 notas musicales (f: frecuencia en Hz [260 a 1100], d: duración en ms [100 a 350]).
                   ¡Compón un motivo musical armónico y pegadizo que refleje la emoción del objeto (pentatónico épico, modo dórico o chiptune vivaz)!
                5. 4 keyframes CSS transform (x, y, scale, rotate) para el holograma.

                Responde ESTRICTAMENTE en JSON con esta estructura exacta:
                {
                  "model": "CYBER-DRAGON",
                  "material": "AERO-TITANIUM",
                  "interpretation": "Dragón cibernético alado",
                  "title": "Protocolo Ícaro",
                  "story_spanish": "En la forja estelar, el autómata cobró aliento mediante impulsos de plasma. Sus alas extendidas refractaron la luz del reactor antes de elevarse al vacío cósmico. Su vuelo inauguró una nueva era para los navegantes celestes.",
                  "primary_rgb": [0, 240, 255],
                  "sec_rgb": [255, 90, 0],
                  "kinematics": [120, 65, 140, 85, 130],
                  "melody": [
                    {"f": 440, "d": 140},
                    {"f": 554, "d": 140},
                    {"f": 659, "d": 160},
                    {"f": 880, "d": 300},
                    {"f": 659, "d": 140},
                    {"f": 880, "d": 350},
                    {"f": 988, "d": 200},
                    {"f": 1046, "d": 400}
                  ],
                  "keyframes": [
                    { "x": 0, "y": -25, "scale": 1.15, "rotate": 8 },
                    { "x": 45, "y": -12, "scale": 0.95, "rotate": -10 },
                    { "x": -40, "y": 18, "scale": 1.12, "rotate": 12 },
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

                # High-fidelity narration synthesis
                tts = client.audio.speech.create(
                    model="tts-1",
                    voice="onyx",
                    input=story_json["story_spanish"]
                )
                st.session_state.audio_bytes = tts.content

                # Dispatch Retained MQTT Payload
                try:
                    publish.single(
                        MQTT_TOPIC,
                        json.dumps(story_json),
                        hostname=MQTT_BROKER,
                        retain=True,
                        keepalive=10
                    )
                except Exception as mqtt_err:
                    st.warning(f"MQTT Status: {mqtt_err}")
    except Exception as e:
        st.error(f"Error en el Taller Cinemático: {e}")

with col_stage:
    st.markdown("##### 🔬 PROYECCIÓN VOLUMÉTRICA & TELEMETRÍA")

    if st.session_state.story_data and st.session_state.drawing_cutout:
        story = st.session_state.story_data
        
        st.markdown(f"### {story.get('title')}")
        st.markdown(f"""
        <div class="mono" style="font-size: 0.8rem; color: #38bdf8; margin-bottom: 10px;">
          CLASSIFICATION: {story.get('model')} // MATERIAL: {story.get('material', 'PLASMA')}
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3", autoplay=True)

        st.markdown(
            f"""
            <div style="background: rgba(15, 23, 42, 0.6); padding: 14px 18px; border-radius: 10px; border-left: 3px solid #38bdf8; font-size: 0.95rem; line-height: 1.6; margin-bottom: 12px; color: #cbd5e1;">
            {story.get('story_spanish')}
            </div>
            """,
            unsafe_allow_html=True
        )

        kf = story.get("keyframes", [])
        anim_css = f"""
        @keyframes holoFloat {{
          0%   {{ transform: translate(0px, 0px) scale(1) rotate(0deg); }}
          25%  {{ transform: translate({kf[0]['x']}px, {kf[0]['y']}px) scale({kf[0]['scale']}) rotate({kf[0]['rotate']}deg); }}
          50%  {{ transform: translate({kf[1]['x']}px, {kf[1]['y']}px) scale({kf[1]['scale']}) rotate({kf[1]['rotate']}deg); }}
          75%  {{ transform: translate({kf[2]['x']}px, {kf[2]['y']}px) scale({kf[2]['scale']}) rotate({kf[2]['rotate']}deg); }}
          100% {{ transform: translate({kf[3]['x']}px, {kf[3]['y']}px) scale({kf[3]['scale']}) rotate({kf[3]['rotate']}deg); }}
        }}
        .holo-chamber {{
          width: 100%;
          height: 220px;
          border-radius: 12px;
          background: radial-gradient(circle at center, #111827 0%, #030712 100%);
          border: 1px solid #1f2937;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          overflow: hidden;
        }}
        .dancing-cutout {{
          max-height: 150px;
          max-width: 150px;
          object-fit: contain;
          animation: holoFloat 6s infinite alternate ease-in-out;
          filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.9)) drop-shadow(0 0 6px #a855f7);
        }}
        """
        stage_html = f"""
        <style>{anim_css}</style>
        <div class="holo-chamber">
          <img src="{st.session_state.drawing_cutout}" class="dancing-cutout"/>
        </div>
        """
        components.html(stage_html, height=230)
    else:
        st.markdown(
            """
            <div style="background: #0f121d; border: 1px dashed #1e293b; border-radius: 12px; height: 380px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 25px;">
                <div style="font-size: 2.2rem; margin-bottom: 8px;">🦾⚡</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #f1f5f9;">CELDA ROBÓTICA EN ESPERA</div>
                <div class="mono" style="font-size: 0.8rem; color: #64748b; max-width: 320px; margin-top: 6px;">
                  1. Activa el sensor óptico en el panel izquierdo.<br>
                  2. Traza un vector o figura en el aire con los dedos.<br>
                  3. Ejecuta "SINTETIZAR" para ensamblar el autómata.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# Embedded Robotic Cell (Diagram View Only)
# ---------------------------------------------------------
st.markdown("---")
col_title, col_link = st.columns([0.8, 0.2])
with col_title:
    st.markdown("##### 🦾 CÉLULA ROBÓTICA CINEMÁTICA EN VIVO // WOKWI ESP32")
    st.caption("🟢 Sincronizado por MQTT. Haz clic en ▶️ en el simulador si está detenido.")
with col_link:
    st.link_button("↗️ Abrir en Wokwi", "https://wokwi.com/projects/479816492813091841")

components.iframe(LIVE_WOKWI_URL, height=620, scrolling=True)
