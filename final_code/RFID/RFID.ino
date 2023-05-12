#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#define SS_PIN D8
#define RST_PIN D0

MFRC522 rfid(SS_PIN, RST_PIN); 
MFRC522::MIFARE_Key key;



WiFiClient vanieriot;
PubSubClient client(vanieriot);

const int pResistor = A0;
int value;

byte nuidPICC[4];

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  Serial.println();
  pinMode(pResistor, INPUT);
  SPI.begin(); 
  rfid.PCD_Init(); 
  Serial.println();
  Serial.print(F("Reader :"));
  rfid.PCD_DumpVersionToSerial();
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }
  Serial.println();
  Serial.println(F("This code scan the MIFARE Classic NUID."));
  Serial.print(F("Using the following key:"));
  printHex(key.keyByte, MFRC522::MF_KEY_SIZE);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  if (!client.loop())
    client.connect("vanieriot");
  lightIntensity();
  if ( ! rfid.PICC_IsNewCardPresent())
    return;
  if ( ! rfid.PICC_ReadCardSerial())
    return;
  Serial.print(F("PICC type: "));
  MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
  Serial.println(rfid.PICC_GetTypeName(piccType));
  if (piccType != MFRC522::PICC_TYPE_MIFARE_MINI &&
      piccType != MFRC522::PICC_TYPE_MIFARE_1K &&
      piccType != MFRC522::PICC_TYPE_MIFARE_4K) {
    Serial.println(F("Your tag is not of type MIFARE Classic."));
    return;
  }

    Serial.println(F("A new card has been detected."));
    // Store NUID into nuidPICC array
    for (byte i = 0; i < 4; i++) {
      nuidPICC[i] = rfid.uid.uidByte[i];
    }
    Serial.println(F("The NUID tag is:"));
    Serial.print(F("In hex: "));
    printHex(rfid.uid.uidByte, rfid.uid.size);


  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();


}

void lightIntensity() {
  value = analogRead(pResistor);
  Serial.println("Light intensity is: ");
  Serial.println(value);
   char pResistorValue[8];
   dtostrf(value, 6,2, pResistorValue); 
    
   client.publish("photo_resistor/lightintensity", pResistorValue);
}


void printHex(byte *buffer, byte bufferSize) {  
  String uid;
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], HEX);
    uid = uid + String(buffer[i], HEX);
  }
  Serial.println("UID : " );
  Serial.print(uid);
  client.publish("esp/rfid", (char*) uid.c_str());

}


void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("WiFi connected - ESP-8266 IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(String topic, byte * message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messagein;

  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messagein += (char)message[i];
  }

}
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("vanieriot")) {
      Serial.println("connected");

    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 3 seconds");
      delay(3000);
    }
  }
}
