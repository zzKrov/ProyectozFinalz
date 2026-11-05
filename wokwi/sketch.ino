#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>

Adafruit_NeoPixel ring(16, 18, NEO_GRB + NEO_KHZ800);
Adafruit_SSD1306 display(128, 64, &Wire, -1);

WiFiClient espClient;
PubSubClient client(espClient);

void setLights(int r, int g, int b) {
  for (int i = 0; i < 16; i++) ring.setPixelColor(i, ring.Color(r, g, b));
  ring.show();
}

void callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  deserializeJson(doc, payload, length);

  int r = doc["r"] | 0;
  int g = doc["g"] | 150;
  int b = doc["b"] | 255;
  const char* headline = doc["headline"] | "Nuevo Cuento";

  setLights(r, g, b);

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10);
  display.println("--- ESCENARIO IA ---");
  display.setCursor(0, 32);
  display.setTextSize(2);
  display.println(headline);
  display.display();
}

void setup() {
  ring.begin();
  setLights(30, 0, 40); // Standby

  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10, 25);
  display.println("Conectando...");
  display.display();

  WiFi.begin("Wokwi-GUEST", "");
  while (WiFi.status() != WL_CONNECTED) delay(200);

  client.setServer("broker.hivemq.com", 1883);
  client.setCallback(callback);

  display.clearDisplay();
  display.setCursor(10, 25);
  display.println("Listo para Dibujar!");
  display.display();
}

void loop() {
  if (!client.connected()) {
    while (!client.connected()) {
      if (client.connect("ESP32_StoryStage_Receiver")) {
        client.subscribe("air_draw_story/stage_cue");
      } else {
        delay(1000);
      }
    }
  }
  client.loop();
}
