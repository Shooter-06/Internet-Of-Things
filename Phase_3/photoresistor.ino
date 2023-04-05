#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Wi-Fi credentials
const char* ssid = "BELL555";
const char* password = "9F4D6E42EA7F";

// MQTT server settings
const char* mqtt_server = "192.168.2.67";
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP8266Client";
const char* mqtt_topic = "lightIntensity";

// Pin for the photoresistor
const int photoresistor_pin = A0;

// Create the Wi-Fi and MQTT client objects
WiFiClient wifi_client;
PubSubClient mqtt_client(wifi_client);

void setup() {
  Serial.begin(115200);
  pinMode(photoresistor_pin, INPUT);

  connect_wifi();
  connect_mqtt();
}

void loop() {
  if (!mqtt_client.connected()) {
    connect_mqtt();
  }

  mqtt_client.loop();

  int light_intensity = analogRead(photoresistor_pin);
  Serial.print("Light: ");
  Serial.print(light_intensity);

  char payload[10];
  snprintf(payload, sizeof(payload), "%d", light_intensity);

  mqtt_client.publish(mqtt_topic, payload);
  delay(1000); // Send light intensity every 1 second
}

void connect_wifi() {
  Serial.print("Connecting to Wi-Fi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Wi-Fi connected");
  Serial.println("IP address: " + WiFi.localIP().toString());
}

void connect_mqtt() {
  Serial.print("Connecting to MQTT server...");
  mqtt_client.setServer(mqtt_server, mqtt_port);

  if (mqtt_client.connect(mqtt_client_id)) {
    Serial.println("connected to " + String(mqtt_server));
  } else {
    Serial.print("failed, rc=");
    Serial.print(mqtt_client.state());
    Serial.println(" try again in 5 seconds");
    delay(5000);
  }
}