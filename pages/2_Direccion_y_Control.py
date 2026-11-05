import streamlit as st
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import json
import time

st.set_page_config(
    page_title="Consola de Dirección y Telemetría",
    page_icon="🎛️",
    layout="wide"
)

st.title("🎛️ Ambiente 2: Consola de Dirección & Telemetría Wokwi")
st.caption("Panel de control técnico, calibración manual de actuadores y monitor de telemetría bidireccional.")

MQTT_BROKER = "broker.hivemq.com"
TOPIC_CUE = "air_draw_story/stage_cue"
TOPIC_TELEMETRY = "air_draw_story/telemetry"

col_ctrl, col_mon = st.columns([1, 1], gap="large")

with col_ctrl:
    st.subheader("1. Mandos Manuales del Escenario")
    st.caption("Controla físicamente el circuito de Wokwi sin pasar por la IA:")

    tab_servos, tab_luces = st.tabs(["🦾 Servomotores", "💡 Iluminación"])

    with tab_servos:
        c1, c2 = st.columns(2)
        with c1:
            telon_izq = st.slider("Telón Izquierdo (Pin 13)", 0, 90, 0, help="0° cerrado, 90° abierto")
            elevador = st.slider("Elevador de Atrezo (Pin 14)", 20, 150, 20, help="20° reposo, 140° escena")
        with c2:
            telon_der = st.slider("Telón Derecho (Pin 25)", 90, 180, 180, help="180° cerrado, 90° abierto")
            viento = st.slider("Máquina de Viento (Pin 27)", 70, 110, 90, help="90° neutro")

    with tab_luces:
        c_sky = st.color_picker("Color Arco Proscenio (Cielo)", "#5A28DC")
        c_foot = st.color_picker("Color Candilejas (Piso)", "#FFA032")
        brillo = st.slider("Intensidad Luminosa (%)", 10, 100, 85)

    if st.button("📡 Enviar Comandos Manuales a Wokwi", type="primary"):
        h_sky = c_sky.lstrip("#")
        rgb_sky = [int(h_sky[i:i+2], 16) for i in (0, 2, 4)]
        h_foot = c_foot.lstrip("#")
        rgb_foot = [int(h_foot[i:i+2], 16) for i in (0, 2, 4)]

        payload = {
            "title": "Mando Manual",
            "score_title": "Intervencion",
            "sky_rgb": rgb_sky,
            "foot_rgb": rgb_foot,
            "intensity": brillo,
            "prop": elevador,
            "melody": [{"f": 262, "d": 200}, {"f": 330, "d": 200}, {"f": 392, "d": 350}]
        }
        try:
            publish.single(TOPIC_CUE, json.dumps(payload), hostname=MQTT_BROKER, retain=True, keepalive=5)
            st.success("✅ Orden transmitida a Wokwi exitosamente.")
        except Exception as e:
            st.error(f"Error de envío: {e}")

with col_mon:
    st.subheader("2. Telemetría de Retorno (Wokwi ➔ Streamlit)")
    st.caption("Verificación del canal de comunicación bidireccional:")

    # Botón para escuchar el canal de retorno de Wokwi
    if st.button("🔄 Consultar Estado de Wokwi"):
        with st.spinner("Escuchando respuesta del ESP32..."):
            received_msg = None
            def on_msg(client, userdata, message):
                nonlocal received_msg
                received_msg = str(message.payload.decode("utf-8"))

            client = mqtt.Client(f"Monitor_{int(time.time())}")
            client.on_message = on_msg
            client.connect(MQTT_BROKER, 1883, 10)
            client.subscribe(TOPIC_TELEMETRY)
            client.loop_start()
            
            # Escucha por 2.5 segundos
            t_end = time.time() + 2.5
            while time.time() < t_end and not received_msg:
                time.sleep(0.1)
            client.loop_stop()

            if received_msg:
                st.success("📡 Paquete recibido desde Wokwi:")
                st.json(json.loads(received_msg))
            else:
                st.info("Sin mensajes recientes en el canal de retorno. Pulsa 'Enviar Comandos' o interactúa con el simulador.")

    st.markdown("""
    ---
    #### Registro de Modalidades Utilizadas
    * **Entrada:** Controles deslizantes (sliders), selectores de color hexadecimal, botones directos.
    * **Canal:** MQTT Full-Duplex (Broker `broker.hivemq.com:1883`).
    * **Tópicos:**
      * Streamlit $\\rightarrow$ Wokwi: `air_draw_story/stage_cue`
      * Wokwi $\\rightarrow$ Streamlit: `air_draw_story/telemetry`
    """)
