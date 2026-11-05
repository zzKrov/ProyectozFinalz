import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import paho.mqtt.publish as publish
import json
import time
import socket
import re
import os

st.set_page_config(
    page_title="El Espejo de las Historias Vivas",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Luminous Glassmorphic Theme (Cohesive & Optimized)
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
    opacity: 0.35;
    animation: driftStars 80s linear infinite;
}
@keyframes driftStars {
    from { transform: translateY(0); }
    to { transform: translateY(-550px); }
}

.header-glow {
    text-align: center;
    padding: 8px 0 14px 0;
    margin-bottom: 18px;
    border-bottom: 1px solid rgba(192, 132, 252, 0.2);
}
.app-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    background: linear-gradient(135deg, #fbcfe8 0%, #c084fc 45%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 20px rgba(192, 132, 252, 0.45));
}
.app-subtitle {
    font-size: 0.92rem;
    color: #cbd5e1;
    margin-top: 2px;
}

.story-card {
    background: rgba(26, 20, 56, 0.65);
    border: 1px solid rgba(192, 132, 252, 0.3);
    box-shadow: 0 8px 32px 0 rgba(112, 0, 255, 0.22);
    backdrop-filter: blur(14px);
    border-radius: 16px;
    padding: 16px 20px;
    margin-top: 8px;
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
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
}
.music-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(192, 132, 252, 0.15);
    color: #c084fc;
    border: 1px solid rgba(192, 132, 252, 0.35);
    margin-left: 6px;
}
.story-body {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    line-height: 1.65;
    color: #e2e8f0;
    margin-top: 6px;
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

div.stButton > button {
    background: rgba(30, 27, 75, 0.7) !important;
    color: #ede6de !important;
    border: 1px solid rgba(192, 132, 252, 0.3) !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    padding: 4px 12px !important;
}
div.stButton > button:hover {
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
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

def send_stage_cue(payload_dict):
    prev_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(3.0)
        publish.single(
            MQTT_TOPIC,
            json.dumps(payload_dict),
            hostname=MQTT_BROKER,
            port=1883,
            retain=True,
            keepalive=5
        )
        st.toast("📡 ¡Partitura transmitida al teatro!", icon="🎼")
        return True
    except Exception as e:
        st.warning(f"Aviso de conexión con el escenario: {e}")
        return False
    finally:
        socket.setdefaulttimeout(prev_timeout)

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
if "ai_model" not in st.session_state:
    st.session_state.ai_model = "gpt-4o-mini"
if "narrator_voice" not in st.session_state:
    st.session_state.narrator_voice = "coral"

# ---------------------------------------------------------
# Header & Settings Drawer
# ---------------------------------------------------------
st.markdown("""
<div class="header-glow">
  <div class="app-title">🎭 El Pequeño Teatro de las Historias Vivas ✨</div>
  <div class="app-subtitle">Dibuja una figura en el aire. La IA compone una partitura original y narra tu aventura mientras el teatro cobra vida.</div>
</div>
""", unsafe_allow_html=True)

with st.expander("⚙️ Ajustes del Narrador & Conexión", expanded=not bool(st.session_state.api_key)):
    cfg_col1, cfg_col2, cfg_col3 = st.columns([1.2, 1, 1])
    with cfg_col1:
        key_input = st.text_input("OpenAI API Key:", value=st.session_state.api_key, type="password", placeholder="sk-...")
        if key_input != st.session_state.api_key:
            st.session_state.api_key = key_input.strip()
            st.rerun()
    with cfg_col2:
        voice_opt = st.selectbox(
            "Voz del Narrador (HD):",
            options=["coral", "fable", "onyx", "nova"],
            index=["coral", "fable", "onyx", "nova"].index(st.session_state.narrator_voice),
            format_func=lambda x: {
                "coral": "Coral (Cálida y Expresiva)",
                "fable": "Fable (Teatral británica)",
                "onyx": "Onyx (Profunda y Épica)",
                "nova": "Nova (Luminosa y Vivaz)"
            }.get(x, x)
        )
        st.session_state.narrator_voice = voice_opt
    with cfg_col3:
        model_opt = st.selectbox(
            "Motor de IA:",
            options=["gpt-4o-mini", "gpt-4o"],
            index=0 if st.session_state.ai_model == "gpt-4o-mini" else 1,
            format_func=lambda x: "Ultrarrápido (gpt-4o-mini ~1.5s)" if "mini" in x else "Alta Definición (gpt-4o)"
        )
        st.session_state.ai_model = model_opt

component_path = os.path.join(os.path.dirname(__file__), "canvas_component")
air_canvas = components.declare_component("air_canvas", path=component_path)

col_draw, col_stage = st.columns([1.0, 1.05], gap="large")

with col_draw:
    current_chapter_num = len(st.session_state.story_chapters) + 1
    st.markdown(f"##### 🪞 El Espejo de Luz &bull; *Capítulo {current_chapter_num}*")
    st.caption("Pellizca el índice y el pulgar para pintar con polvo de estrellas.")
    canvas_output = air_canvas(default=None, key="air_canvas_ui")

# ---------------------------------------------------------
# Sequential Storytelling & Fast Composition Pipeline
# ---------------------------------------------------------
if canvas_output:
    try:
        data = json.loads(canvas_output) if isinstance(canvas_output, str) else canvas_output
        action_id = data.get("id")

        if not st.session_state.api_key:
            st.error("⚠️ Ingresa tu OpenAI API Key en los ajustes superiores para despertar la historia.")
        elif action_id and action_id != st.session_state.processed_id:
            cutout_img = data.get("cutout")
            vision_raw = data.get("vision", "")
            base64_data = vision_raw.split(",")[1] if "," in vision_raw else vision_raw

            with st.spinner(f"🎼 Componiendo partitura y tejiendo el Capítulo {current_chapter_num}..."):
                client = OpenAI(api_key=st.session_state.api_key)

                history_prompt = ""
                if st.session_state.story_chapters:
                    history_prompt = "HISTORIA HASTA EL MOMENTO:\n"
                    for ch in st.session_state.story_chapters:
                        history_prompt += f"- Capítulo {ch['num']} ({ch['title']}): {ch['text']}\n"
                else:
                    history_prompt = "Este es el comienzo de una nueva aventura mágica.\n"

                prompt = f"""
                Eres simultáneamente el Narrador Dramático y el Maestro Compositor Musical de un Teatro de Marionetas.
                {history_prompt}

                EL USUARIO ACABA DE DIBUJAR UN NUEVO ELEMENTO EN EL AIRE (mira la imagen adjunta).

                INSTRUCCIONES DE NARRATIVA EMOCIONAL:
                1. Identifica qué criatura u objeto dibujó el usuario.
                2. Escribe el CAPÍTULO {current_chapter_num} de la historia en ESPAÑOL (2 a 3 oraciones ricas en expresividad). Continuación fluida de los capítulos previos.
                3. MODULACIÓN VOCAL RICA: Usa signos de puntuación dramática (puntos suspensivos '...' para misterio, exclamaciones '¡!', guiones largos '—' para pausas solemnes, comas fluidas) para que la voz modulada exprese emoción viva, asombro y matices.
                4. Asigna un título poético (máx. 25 letras).

                INSTRUCCIONES DE COMPOSICIÓN MUSICAL (PARTITURA ORIGINAL):
                5. Bautiza la pieza musical con un título evocador (ej: "Danza del Viento", "Nana de la Luna", "Marcha de las Estrellas").
                6. Carácter emocional breve (ej: "Lírico y Soñador", "Misterioso", "Jovial").
                7. COMPÓN UNA MELODÍA ARMÓNICA Y REAL de 8 a 14 notas musicales.
                   REGLA OBLIGATORIA DE FRECUENCIAS (Cajita de música cálida, tonos graves y medios, NUNCA chirridos agudos):
                   - Usa EXCLUSIVAMENTE notas afinadas de la escala pentatónica:
                     G3: 196 Hz | A3: 220 Hz | B3: 247 Hz | C4: 262 Hz | D4: 294 Hz | E4: 330 Hz | F4: 349 Hz | G4: 392 Hz | A4: 440 Hz | C5: 523 Hz
                     (Usa 0 para silencios y pausas rítmicas indispensables).
                   - Duraciones en ms: 180 (ligera), 280 (media), 450 (nota reposada final).
                   - Concluye la melodía reposando en la tónica (C4: 262 o G3: 196).

                8. Parámetros del escenario mecánico:
                   - sky_rgb: [R, G, B] color del cielo/arco superior.
                   - foot_rgb: [R, G, B] color cálido de las candilejas de suelo.
                   - intensity: brillo de 65 a 90.
                   - prop: elevación del atrezo (40 para rastreros, 90 para caminantes, 140 para voladores/mágicos).

                Responde ÚNICAMENTE en JSON con esta estructura:
                {{
                  "entity": "nombre del elemento",
                  "title": "Título del Capítulo",
                  "story_spanish": "Cuento en español con puntuación expresiva...",
                  "score_title": "Nombre de la Canción",
                  "score_mood": "Carácter emocional",
                  "sky_rgb": [90, 40, 220],
                  "foot_rgb": [255, 170, 50],
                  "intensity": 85,
                  "prop": 120,
                  "melody": [
                    {{"f": 262, "d": 280}},
                    {{"f": 330, "d": 280}},
                    {{"f": 392, "d": 450}},
                    {{"f": 0, "d": 90}},
                    {{"f": 440, "d": 260}},
                    {{"f": 392, "d": 260}},
                    {{"f": 330, "d": 450}}
                  ]
                }}
                """

                # Light-speed inference
                completion = client.chat.completions.create(
                    model=st.session_state.ai_model,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un narrador de cuentos teatrales expresivo y compositor musical. Respondes exclusivamente en formato JSON válido."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}}
                            ]
                        }
                    ]
                )

                choice = completion.choices[0]
                message = choice.message

                if getattr(message, "refusal", None):
                    raise ValueError(f"El modelo no pudo procesar la figura: {message.refusal}")

                raw_content = message.content
                if not raw_content:
                    raise ValueError(f"Respuesta vacía del modelo (motivo: {choice.finish_reason}).")

                match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                clean_json = match.group(0) if match else raw_content.strip()
                chapter_data = json.loads(clean_json)

                # High-Fidelity Voice Synthesis (tts-1-hd with voice modulation)
                story_text = chapter_data.get("story_spanish", "Había una vez una figura mágica que cobró vida.")
                tts = client.audio.speech.create(
                    model="tts-1-hd",
                    voice=st.session_state.narrator_voice,
                    input=story_text
                )
                audio_bytes = tts.content

                # Register state
                st.session_state.processed_id = action_id
                st.session_state.current_cutout = cutout_img
                st.session_state.current_audio = audio_bytes

                st.session_state.story_chapters.append({
                    "num": current_chapter_num,
                    "title": chapter_data.get("title", f"Capítulo {current_chapter_num}"),
                    "score_title": chapter_data.get("score_title", "Melodía Mágica"),
                    "score_mood": chapter_data.get("score_mood", "Encantador"),
                    "entity": chapter_data.get("entity", "Creación mágica"),
                    "text": story_text,
                    "cutout": cutout_img,
                    "audio": audio_bytes
                })

                stage_payload = {
                    "title": chapter_data.get("title", f"Capítulo {current_chapter_num}"),
                    "score_title": chapter_data.get("score_title", "Melodía Mágica"),
                    "sky_rgb": chapter_data.get("sky_rgb", [90, 40, 220]),
                    "foot_rgb": chapter_data.get("foot_rgb", [255, 170, 50]),
                    "intensity": chapter_data.get("intensity", 85),
                    "prop": chapter_data.get("prop", 120),
                    "melody": chapter_data.get("melody", [])
                }

                send_stage_cue(stage_payload)
                st.rerun()

    except Exception as err:
        st.error(f"❌ Error al generar historia: {err}")

with col_stage:
    col_st_title, col_btns = st.columns([0.55, 0.45])
    with col_st_title:
        st.markdown("##### 🎪 El Escenario Mecatrónico en Vivo")
    with col_btns:
        btn_c1, btn_c2, btn_c3 = st.columns(3)
        with btn_c1:
            if st.button("🔔 Probar", help="Envía una partitura de prueba a Wokwi"):
                test_cue = {
                    "title": "Acto de Prueba",
                    "score_title": "Danza de Prueba",
                    "sky_rgb": [0, 240, 255],
                    "foot_rgb": [255, 120, 40],
                    "intensity": 90,
                    "prop": 135,
                    "melody": [
                        {"f": 262, "d": 260},
                        {"f": 330, "d": 260},
                        {"f": 392, "d": 380},
                        {"f": 0,   "d": 80},
                        {"f": 523, "d": 450}
                    ]
                }
                send_stage_cue(test_cue)
        with btn_c2:
            if st.button("🔄 Sync", help="Fuerza a recargar el simulador Wokwi"):
                st.session_state.wokwi_session_token = int(time.time())
                st.rerun()
        with btn_c3:
            if st.session_state.story_chapters:
                if st.button("✨ Reset"):
                    st.session_state.story_chapters = []
                    st.session_state.current_cutout = None
                    st.session_state.current_audio = None
                    st.session_state.processed_id = None
                    st.rerun()

    st.caption("💡 *Asegúrate de pulsar el botón verde ▶️ (Play) dentro de Wokwi para encender el escenario.*")

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
          <div>
            <span class="chapter-badge">Capítulo {latest['num']} &bull; {latest['entity']}</span>
            <span class="music-badge">🎼 {latest.get('score_title', 'Partitura')} ({latest.get('score_mood', 'Mágico')})</span>
          </div>
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
          <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">Dibuja la primera criatura o paisaje para abrir el telón y escuchar su música original.</div>
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
            st.caption(f"🎼 *{ch.get('score_title', 'Canción')}*")
            if ch.get("cutout"):
                st.image(ch["cutout"], width=90)
            st.caption(ch["text"])
