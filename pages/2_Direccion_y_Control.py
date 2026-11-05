import streamlit as st
import paho.mqtt.publish as publish
import json, socket, time

st.set_page_config(
    page_title="Ambiente 2: Dirección y Telemetría",
    page_icon="🎛️",
    layout="wide"
)

st.title("🎛️ Ambiente 2: Dirección Técnica & Telemetría Wokwi")
st.caption("Página satélite para control manual de actuadores y telemetría bidireccional.")

MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "air_draw_story/stage_cue"

c1, c2 = st.columns(2)
with c1:
    st.subheader("Calibración Manual de Servomotores")
    ang_l = st.slider("Telón Izquierdo (Pin 13)", 0, 90, 0)
    ang_r = st.slider("Telón Derecho (Pin 25)", 90, 180, 180)
    ang_prop = st.slider("Elevador de Atrezo (Pin 14)", 20, 150, 120)
    ang_wind = st.slider("Máquina de Viento (Pin 27)", 70, 110, 90)

with c2:
    st.subheader("Iluminación Proscenio")
    col_sky = st.color_picker("Color Arco Cielo", "#5A28DC")
    col_foot = st.color_picker("Color Candilejas", "#FFA032")
    intensity = st.slider("Brillo General (%)", 10, 100, 85)

if st.button("📡 Transmitir Órdenes a Wokwi", type="primary"):
    h_sky = col_sky.lstrip("#")
    rgb_sky = [int(h_sky[i:i+2], 16) for i in (0, 2, 4)]
    h_foot = col_foot.lstrip("#")
    rgb_foot = [int(h_foot[i:i+2], 16) for i in (0, 2, 4)]
    
    payload = {
        "title": "Mando Manual",
        "score_title": "Intervencion",
        "sky_rgb": rgb_sky,
        "foot_rgb": rgb_foot,
        "intensity": intensity,
        "prop": ang_prop,
        "melody": [{"f": 262, "d": 200}, {"f": 330, "d": 200}, {"f": 392, "d": 350}]
    }
    try:
        socket.setdefaulttimeout(3.0)
        publish.single(MQTT_TOPIC, json.dumps(payload), hostname=MQTT_BROKER, port=1883, retain=True)
        st.success("✅ Orden transmitida con éxito a Wokwi.")
    except Exception as e:
        st.error(f"Error de enlace: {e}")
