#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <Adafruit_SSD1306.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

#define NEO_PIN     18
#define SERVO1_PIN  13
#define SERVO2_PIN  14
#define BUZZER_PIN  23

Adafruit_NeoPixel ring(16, NEO_PIN, NEO_GRB + NEO_KHZ800);
Adafruit_SSD1306 display(128, 64, &Wire, -1);
Servo rotorArm1;
Servo rotorArm2;

WiFiClient espClient;
PubSubClient client(espClient);

bool isAnimating = false;
unsigned long animStartTime = 0;

void playMagicChime() {
  tone(BUZZER_PIN, 523, 100); delay(120);
  tone(BUZZER_PIN, 659, 100); delay(120);
  tone(BUZZER_PIN, 784, 150); delay(180);
  tone(BUZZER_PIN, 1046, 250); delay(250);
  noTone(BUZZER_PIN);
}

void setLights(int r, int g, int b) {
  for (int i = 0; i < 16; i++) ring.setPixelColor(i, ring.Color(r, g, b));
  ring.show();
}

void callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<384> doc;
  deserializeJson(doc, payload, length);

  int r = doc["r"] | 0;
  int g = doc["g"] | 200;
  int b = doc["b"] | 255;
  const char* headline = doc["headline"] | "Cuento Activo";

  setLights(r, g, b);

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 8);
  display.println("--- ESCENARIO VIVO ---");
  display.setCursor(0, 30);
  display.setTextSize(2);
  display.println(headline);
  display.display();

  playMagicChime();

  // Trigger 8 seconds of physical rotor animatronic dance
  isAnimating = true;
  animStartTime = millis();
}

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);

  rotorArm1.attach(SERVO1_PIN);
  rotorArm2.attach(SERVO2_PIN);
  rotorArm1.write(90);
  rotorArm2.write(90);

  ring.begin();
  setLights(40, 0, 40); // Standby purple

  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(5, 25);
  display.println("Conectando WiFi...");
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
      if (client.connect("ESP32_Animatronics_Stage")) {
        client.subscribe("air_draw_story/stage_cue");
      } else {
        delay(1000);
      }
    }
  }
  client.loop();

  // Physical Rotor Dancing Routine
  if (isAnimating) {
    if (millis() - animStartTime < 8000) {
      float t = (millis() - animStartTime) / 250.0;
      int angle1 = 90 + sin(t) * 70;
      int angle2 = 90 + cos(t * 1.3) * 70;
      rotorArm1.write(constrain(angle1, 10, 170));
      rotorArm2.write(constrain(angle2, 10, 170));
      delay(20);
    } else {
      rotorArm1.write(90);
      rotorArm2.write(90);
      isAnimating = false;
    }
  }
}
