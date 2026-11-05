import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import os

st.set_page_config(page_title="Air-Drawing Storyteller", layout="wide")

# Register custom component
component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

st.title("🪄 Air-Drawing Storyteller (MediaPipe + OpenAI + Wokwi)")
st.caption("Dibuja en el aire pellizcando tus dedos. La IA interpretará tu trazo, creará un cuento narrado en español y animará los objetos.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    default_key = st.secrets.get("OPENAI_API_KEY", "")
    api_key = st.text_input("OpenAI API Key", value=default_key, type="password")
    mqtt_broker = st.text_input("Broker MQTT (Wokwi)", value="broker.hivemq.com")
    st.markdown("""
    ---
    **Instrucciones de uso:**
    1. Haz clic en **🎥 Iniciar Cámara** y permite el acceso en tu navegador.
    2. Junta el pulgar y el índice para pintar en el aire.
    3. Sepáralos para flotar el lápiz sin dibujar.
    4. Haz clic en **✨ Enviar Dibujo a OpenAI**.
    """)

# Session State Initialization
if "drawing_data" not in st.session_state:
    st.session_state.drawing_data = None
if "story_data" not in st.session_state:
    st.session_state.story_data = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

col_draw, col_story = st.columns([1.1, 0.9])

with col_draw:
    st.subheader("1. Pizarra de Dibujo Aéreo")
    returned_data = air_canvas(default=None, key="air_canvas_ui")
    if returned_data:
        st.session_state.drawing_data = returned_data

with col_story:
    st.subheader("2. Cuento Animado & Escenario")

    if not st.session_state.drawing_data:
        st.info("👈 Presiona **🎥 Iniciar Cámara** a la izquierda. Cuando termines tu figura aérea, pulsa **✨ Enviar Dibujo a OpenAI**.")
    else:
        st.image(st.session_state.drawing_data, caption="Trazo actual capturado", width=280)

        if st.button("🚀 Crear Cuento y Animar", type="primary"):
            if not api_key:
                st.error("Debes ingresar una OpenAI API Key en la barra lateral.")
            else:
                client = OpenAI(api_key=api_key)
                base64_img = st.session_state.drawing_data.split(",")[1]

                with st.spinner("🧠 gpt-4o interpretando dibujo y dirigiendo la escena..."):
                    prompt = """
                    Eres un director de animación y narrador de cuentos infantiles.
                    Analiza la imagen dibujada en el aire:
                    1. Identifica qué objeto, criatura o personaje dibujó el usuario.
                    2. Inventa un breve cuento mágico e inmersivo en ESPAÑOL (máximo 4 oraciones).
                    3. Genera 4 keyframes de animación CSS transform (translateX, translateY en px, scale, rotate en deg).
                    4. Define el color ambiental para Wokwi (RGB) y un título corto (máximo 16 caracteres).

                    Responde estrictamente en formato JSON:
                    {
                      "interpretation": "objeto reconocido",
                      "title": "Título Corto",
                      "story_spanish": "Había una vez...",
                      "stage_cue": { "r": 255, "g": 100, "b": 0, "headline": "Aventura" },
                      "keyframes": [
                        { "x": 0, "y": -25, "scale": 1.15, "rotate": 10 },
                        { "x": 70, "y": -50, "scale": 0.9, "rotate": -12 },
                        { "x": -50, "y": 20, "scale": 1.2, "rotate": 15 },
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

                # Text-to-Speech
                with st.spinner("🎙️ Generando narración en español..."):
                    tts = client.audio.speech.create(
                        model="tts-1",
                        voice="nova",
                        input=st.session_state.story_data["story_spanish"]
                    )
                    st.session_state.audio_bytes = tts.content

                # MQTT Stage Trigger
                try:
                    publish.single(
                        "air_draw_story/stage_cue",
                        json.dumps(st.session_state.story_data["stage_cue"]),
                        hostname=mqtt_broker,
                        keepalive=5
                    )
                    st.success("💡 ¡Escenario físico en Wokwi sincronizado!")
                except Exception as e:
                    st.warning(f"Aviso Wokwi (MQTT): {e}")

    # Display Story, Audio and Keyframe Animation
    if st.session_state.story_data:
        story = st.session_state.story_data
        st.markdown(f"### 📖 {story.get('title')}")
        st.write(f"**Identificado:** {story.get('interpretation')}")
        st.info(story.get("story_spanish"))

        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3", autoplay=True)

        kf = story.get("keyframes", [])
        anim_css = f"""
        @keyframes airAnimation {{
          0%   {{ transform: translate(0px, 0px) scale(1) rotate(0deg); }}
          25%  {{ transform: translate({kf[0]['x']}px, {kf[0]['y']}px) scale({kf[0]['scale']}) rotate({kf[0]['rotate']}deg); }}
          50%  {{ transform: translate({kf[1]['x']}px, {kf[1]['y']}px) scale({kf[1]['scale']}) rotate({kf[1]['rotate']}deg); }}
          75%  {{ transform: translate({kf[2]['x']}px, {kf[2]['y']}px) scale({kf[2]['scale']}) rotate({kf[2]['rotate']}deg); }}
          100% {{ transform: translate({kf[3]['x']}px, {kf[3]['y']}px) scale({kf[3]['scale']}) rotate({kf[3]['rotate']}deg); }}
        }}
        .stage {{
          width: 100%;
          height: 250px;
          background: radial-gradient(circle, #252836 0%, #0d1117 100%);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid #30363d;
          overflow: hidden;
        }}
        .drawing-sprite {{
          max-height: 180px;
          animation: airAnimation 7s infinite alternate ease-in-out;
          filter: drop-shadow(0 0 12px rgba(0, 242, 254, 0.7));
        }}
        """
        stage_html = f"""
        <style>{anim_css}</style>
        <div class="stage">
          <img src="{st.session_state.drawing_data}" class="drawing-sprite"/>
        </div>
        """
        components.html(stage_html, height=270)
