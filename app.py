import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import os

st.set_page_config(page_title="Multimodal Air-Storyteller", layout="wide")

component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

st.title("🪄 Air-Drawing Storyteller (MediaPipe + OpenAI + Wokwi)")
st.caption("Dibuja en el aire pellizcando tus dedos. Tu personaje recortado bailará en escena mientras los rotores físicos de Wokwi reaccionan.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    default_key = st.secrets.get("OPENAI_API_KEY", "")
    api_key = st.text_input("OpenAI API Key", value=default_key, type="password")
    mqtt_broker = st.text_input("Broker MQTT", value="broker.hivemq.com")
    
    st.markdown("### 🎪 Simulación Wokwi")
    wokwi_project_id = st.text_input(
        "ID de Proyecto Wokwi",
        value="",
        placeholder="Ej: 395012345678901234",
        help="Copia el número que aparece al final de la URL de tu proyecto en wokwi.com"
    )
    
    st.markdown("""
    ---
    **Instrucciones:**
    1. Presiona **🎥 Iniciar Cámara**.
    2. Junta pulgar e índice para pintar en el aire.
    3. Pulsa **✨ Enviar Recorte a OpenAI**.
    4. Observa cómo baila tu figura recortada y giran los rotores de Wokwi.
    """)

# State variables
if "drawing_cutout" not in st.session_state:
    st.session_state.drawing_cutout = None
if "drawing_vision" not in st.session_state:
    st.session_state.drawing_vision = None
if "story_data" not in st.session_state:
    st.session_state.story_data = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# Top Section: Drawing and Animated Stage
col_draw, col_story = st.columns([1.1, 0.9])

with col_draw:
    st.subheader("1. Pizarra de Dibujo Aéreo")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")
    
    if canvas_output:
        try:
            parsed = json.loads(canvas_output)
            st.session_state.drawing_cutout = parsed.get("cutout")
            st.session_state.drawing_vision = parsed.get("vision")
        except Exception:
            pass

with col_story:
    st.subheader("2. Cuento Animado & Personaje Recortado")

    if not st.session_state.drawing_cutout:
        st.info("👈 Presiona **🎥 Iniciar Cámara** a la izquierda. Cuando dibujes tu personaje en el aire, pulsa **✨ Enviar Recorte a OpenAI**.")
    else:
        st.markdown("**Personaje extraído (recorte transparente):**")
        st.image(st.session_state.drawing_cutout, width=160)

        if st.button("🚀 Crear Cuento y Animar", type="primary"):
            if not api_key:
                st.error("Ingresa tu OpenAI API Key en la barra lateral.")
            else:
                client = OpenAI(api_key=api_key)
                base64_img = st.session_state.drawing_vision.split(",")[1]

                with st.spinner("🧠 gpt-4o reconociendo figura y componiendo animación..."):
                    prompt = """
                    Analiza la figura dibujada por el usuario:
                    1. Identifica qué objeto, criatura o personaje es.
                    2. Escribe un micro-cuento infantil fantástico y divertido en ESPAÑOL (máximo 4 oraciones).
                    3. Define 4 keyframes de animación CSS transform (x en px [-70 a 70], y en px [-40 a 40], scale [0.8 a 1.3], rotate en deg [-25 a 25]).
                    4. Define color RGB ambiental para los LEDs de Wokwi y un título de máximo 16 letras.

                    Responde ÚNICAMENTE en JSON:
                    {
                      "interpretation": "objeto identificado",
                      "title": "Título Corto",
                      "story_spanish": "Había una vez...",
                      "stage_cue": { "r": 255, "g": 120, "b": 0, "headline": "Dragon Magico" },
                      "keyframes": [
                        { "x": 0, "y": -30, "scale": 1.15, "rotate": 12 },
                        { "x": 60, "y": -15, "scale": 0.9, "rotate": -10 },
                        { "x": -50, "y": 25, "scale": 1.25, "rotate": 18 },
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
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                            ]
                        }]
                    )
                    st.session_state.story_data = json.loads(completion.choices[0].message.content)

                with st.spinner("🎙️ Generando narración en audio..."):
                    tts = client.audio.speech.create(
                        model="tts-1",
                        voice="nova",
                        input=st.session_state.story_data["story_spanish"]
                    )
                    st.session_state.audio_bytes = tts.content

                # Send cue to Wokwi via MQTT (triggers NeoPixel, Buzzer, and Servo dance)
                try:
                    publish.single(
                        "air_draw_story/stage_cue",
                        json.dumps(st.session_state.story_data["stage_cue"]),
                        hostname=mqtt_broker,
                        keepalive=5
                    )
                    st.success("⚡ ¡Rotores y luces de Wokwi activados!")
                except Exception as e:
                    st.warning(f"Aviso Wokwi (MQTT): {e}")

    # Display Story, Voice and Dancing Cutout
    if st.session_state.story_data:
        story = st.session_state.story_data
        st.markdown(f"### 📖 {story.get('title')}")
        st.write(f"**Identificado:** `{story.get('interpretation')}`")
        st.info(story.get("story_spanish"))

        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3", autoplay=True)

        kf = story.get("keyframes", [])
        anim_css = f"""
        @keyframes cutoutDance {{
          0%   {{ transform: translate(0px, 0px) scale(1) rotate(0deg); }}
          25%  {{ transform: translate({kf[0]['x']}px, {kf[0]['y']}px) scale({kf[0]['scale']}) rotate({kf[0]['rotate']}deg); }}
          50%  {{ transform: translate({kf[1]['x']}px, {kf[1]['y']}px) scale({kf[1]['scale']}) rotate({kf[1]['rotate']}deg); }}
          75%  {{ transform: translate({kf[2]['x']}px, {kf[2]['y']}px) scale({kf[2]['scale']}) rotate({kf[2]['rotate']}deg); }}
          100% {{ transform: translate({kf[3]['x']}px, {kf[3]['y']}px) scale({kf[3]['scale']}) rotate({kf[3]['rotate']}deg); }}
        }}
        .stage-box {{
          width: 100%;
          height: 250px;
          background: radial-gradient(circle at center, #1f2937 0%, #0b0f17 100%);
          border-radius: 12px;
          border: 1px solid #374151;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          position: relative;
        }}
        .dancing-cutout {{
          max-height: 160px;
          max-width: 160px;
          object-fit: contain;
          animation: cutoutDance 6s infinite alternate ease-in-out;
          filter: drop-shadow(0 0 16px rgba(0, 242, 254, 0.9));
        }}
        """
        stage_html = f"""
        <style>{anim_css}</style>
        <div class="stage-box">
          <img src="{st.session_state.drawing_cutout}" class="dancing-cutout"/>
        </div>
        """
        components.html(stage_html, height=270)

# ---------------------------------------------------------
# Bottom Section: Embedded Live Wokwi Stage
# ---------------------------------------------------------
st.markdown("---")
st.subheader("🎪 Escenario Físico Wokwi en Vivo (Animatronics & Iluminación)")

if wokwi_project_id.strip():
    wokwi_url = f"https://wokwi.com/projects/{wokwi_project_id.strip()}"
    components.iframe(wokwi_url, height=520, scrolling=True)
else:
    st.info(
        "💡 **Para ver Wokwi dentro de la app:**\n"
        "1. Crea tu proyecto en [wokwi.com](https://wokwi.com/) y guárdalo.\n"
        "2. Copia el ID numérico de la barra de direcciones (ej: `395012345678901234`).\n"
        "3. Pégalo en el campo **'ID de Proyecto Wokwi'** en la barra lateral izquierda."
    )
