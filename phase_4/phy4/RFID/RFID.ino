#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ESP8266SMTP.h>

#define SS_PIN D8
#define RST_PIN D0

MFRC522 rfid(SS_PIN, RST_PIN); // Instance of the class
MFRC522::MIFARE_Key key;

const char* ssid = "TP-Link_2AD8";
const char* password = "14730078";
const char* mqtt_server = "192.168.0.195";
const char* email_server = "smtp.gmail.com";
const int email_port = 587;
const char* email_sender = "john190curry@gmail.com";
const char* email_password = "CUURY23JOHN45";
const char* email_recipient = "john190curry@gmail.com";

WiFiClient wifiClient;
PubSubClient client(wifiClient);

// light setup
const int pResistor = A0;
int value;

// Init array that will store new NUID
byte nuidPICC[4];

ESP8266SMTP smtp(email_server, email_port);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("WiFi connected");
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  Serial.println();
  pinMode(pResistor, INPUT);
  SPI.begin(); // Init SPI bus
  rfid.PCD_Init(); // Init MFRC522
  Serial.println();
  Serial.print(F("Reader: "));
  
  rfid.PCD_DumpVersionToSerial();
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }
  Serial.println();
  Serial.println(F("This code scans the MIFARE Classic NUID."));
  Serial.print(F("Using the following key:"));
  printHex(key.keyByte, MFRC522::MF_KEY_SIZE);
  smtp.enableDebugging(true);
  smtp.startTLS(email_sender, email_password, email_server);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  if (!client.loop())
    client.connect("vanieriot");
  lightIntensity();
  // Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
  if ( ! rfid.PICC_IsNewCardPresent())
    return;
  // Verify if the NUID has been readed
  if ( ! rfid.PICC_ReadCardSerial())
    return;
  Serial.print(F("PICC type: "));
  MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
  Serial.println(rfid.PICC_GetTypeName(piccType));
  // Check is the PICC of Classic MIFARE type
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
  //get value of the light intensity
  value = analogRead(pResistor);

//  digitalWrite(ledPin, LOW);
  Serial.println("Light intensity is: ");
  Serial.println(value);

   //publish value
   char pResistorValue[8];
   dtostrf(value, 6,2, pResistorValue); 
    
   client.publish("esp/lightintensity", pResistorValue);
//   client.publish("esp/lightswitch", ledStatus);
}

/**
  Helper routine to dump a byte array as hex values to Serial.
*/
void printHex(byte *buffer, byte bufferSize) {  
  String uid;
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], HEX);
    uid = uid + String(buffer[i], HEX);
  }
  Serial.println("UID CHILKA: " );
  Serial.print(uid);
  client.publish("esp/rfid", (char*) uid.c_str());

}


void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
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
      // Wait 5 seconds before retrying
      delay(3000);
    }
  }
}  
