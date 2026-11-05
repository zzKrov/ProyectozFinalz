import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import os

st.set_page_config(page_title="MediaPipe Air-Storyteller", layout="wide")

# Register custom component
component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

st.title("🪄 Air-Drawing Storyteller (MediaPipe + OpenAI + Wokwi)")
st.caption("Dibuja en el aire pellizcando tus dedos. La IA interpretará tu dibujo, compondrá un cuento narrado en español y animará tus trazos.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    default_key = st.secrets.get("OPENAI_API_KEY", "")
    api_key = st.text_input("OpenAI API Key", value=default_key, type="password")
    mqtt_broker = st.text_input("Broker MQTT (Wokwi)", value="broker.hivemq.com")
    st.markdown("""
    ---
    **Instrucciones:**
    1. Permite el acceso a la cámara.
    2. Junta el pulgar y el índice para dibujar.
    3. Suelta para mover el cursor en el aire.
    4. Haz clic en **Enviar Dibujo a OpenAI**.
    """)

col_draw, col_story = st.columns([1.1, 0.9])

with col_draw:
    st.subheader("1. Pizarra de Dibujo Aéreo")
    # Bi-directional component: receives dataURL when user clicks 'Enviar'
    drawing_data = air_canvas()

with col_story:
    st.subheader("2. Cuento Animado & Escenario")

    if drawing_data:
        st.image(drawing_data, caption="Trazo capturado", width=280)

        if st.button("🚀 Crear Cuento y Animar", type="primary"):
            if not api_key:
                st.error("Debes ingresar una OpenAI API Key en la barra lateral.")
            else:
                client = OpenAI(api_key=api_key)
                base64_img = drawing_data.split(",")[1]

                with st.spinner("🧠 gpt-4o analizando dibujo y dirigiendo la escena..."):
                    prompt = """
                    Eres un director de animación y narrador de cuentos infantiles.
                    Analiza la imagen dibujada en el aire:
                    1. Identifica el objeto o personaje dibujado.
                    2. Escribe una historia mágica, breve e inmersiva en ESPAÑOL (máximo 4 oraciones).
                    3. Genera 4 keyframes de animación CSS transform (translateX, translateY en px, scale, rotate en deg).
                    4. Escoge un color RGB ambiental para el escenario Wokwi y un título de máximo 16 letras.

                    Responde EXCLUSIVAMENTE en JSON:
                    {
                      "interpretation": "objeto reconocido",
                      "title": "Título Breve",
                      "story_spanish": "Cuento en español...",
                      "stage_cue": { "r": 255, "g": 80, "b": 0, "headline": "Aventura" },
                      "keyframes": [
                        { "x": 0, "y": -30, "scale": 1.15, "rotate": 12 },
                        { "x": 90, "y": -60, "scale": 0.9, "rotate": -10 },
                        { "x": -60, "y": 20, "scale": 1.2, "rotate": 15 },
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
                    story_data = json.loads(completion.choices[0].message.content)
                    st.session_state["story_data"] = story_data

                # Text to Speech narration in Spanish
                with st.spinner("🎙️ Generando narración de voz en español..."):
                    tts = client.audio.speech.create(
                        model="tts-1",
                        voice="nova",
                        input=story_data["story_spanish"]
                    )
                    st.session_state["audio_bytes"] = tts.content

                # Multimodal Sync with Wokwi via MQTT
                try:
                    publish.single(
                        "air_draw_story/stage_cue",
                        json.dumps(story_data["stage_cue"]),
                        hostname=mqtt_broker
                    )
                    st.success("💡 ¡Escenario físico en Wokwi sincronizado!")
                except Exception as e:
                    st.warning(f"MQTT Wokwi no respondió: {e}")

    # Render results
    if "story_data" in st.session_state:
        data = st.session_state["story_data"]
        st.markdown(f"### 📖 {data.get('title')}")
        st.write(f"**Identificado:** {data.get('interpretation')}")
        st.info(data.get("story_spanish"))

        if "audio_bytes" in st.session_state:
            st.audio(st.session_state["audio_bytes"], format="audio/mp3", autoplay=True)

        # Dynamic Keyframe Animation
        kf = data.get("keyframes", [])
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
          height: 240px;
          background: radial-gradient(circle, #252836 0%, #111319 100%);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          border: 1px solid #333;
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
          <img src="{drawing_data}" class="drawing-sprite"/>
        </div>
        """
        components.html(stage_html, height=260)
