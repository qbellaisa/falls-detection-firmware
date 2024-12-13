/*
 * Programa:
 * Autora: Isabella Cabral
 * Data: Fevereiro/2022
 */

// ---- WiFi -------
#include <WiFi.h>
const char* ssid     = "Isabella";
const char* password = "cbrl30071319";
WiFiClient esp32Client;

// ---- MQTT -------
#include <PubSubClient.h>
#include <ArduinoJson.h> 
PubSubClient MQTT(esp32Client);
const char* mqtt_server = "10.0.0.11";
const uint16_t mqtt_port = 1883;
const char* mqtt_ClientID = "esp32";
const char* mqtt_user = "esp32";
const char* mqtt_pass = "monitora";
const char* mqtt_pub_Topic = "ESP32/MPU6050";;

//Declaracao das variaveis que armazenam os Aliases das variaveis da plataforma
const char ALIAS1[] = "AccelX";
const char ALIAS2[] = "AccelY";
const char ALIAS3[] = "AccelZ";
const char ALIAS4[] = "GyroX"; 
const char ALIAS5[] = "GyroY";
const char ALIAS6[] = "GyroZ";

//Declaracao da variavel que armazena o intervalo de tempo entre mensagens
unsigned long reconecta; //Variavel para a conexao com o servidor

// ---- MPU6050 -------
#include <Wire.h>         // biblioteca de comunicação I2C
#include <MPU6050_tockn.h>
MPU6050 mpu6050(Wire);
float AcX, AcY, AcZ, GyX, GyY, GyZ; 

const int sda_pin = 21; // definição do pino I2C SDA
const int scl_pin = 22; // definição do pino I2C SCL
 
// --------------------------------------------------------------------------------
void setup() 
{
  Serial.begin(115200);
  delay(100);
 
  Serial.println("Iniciando conexão WiFi");
  connectWifi();
  delay(100);

  Serial.print("Servidor configurado: ");
  Serial.print(mqtt_server);
  Serial.print(" : ");
  Serial.println(mqtt_port);
  MQTT.setServer(mqtt_server, mqtt_port);
  delay(100);
  
  Serial.println("Iniciando configuração e calibração do MPU6050");
  Wire.begin(sda_pin, scl_pin);
  mpu6050.begin();
  mpu6050.calcGyroOffsets(true);
  delay(100);
}

void getMPUData()
{
  mpu6050.update();
  Serial.println("\n=======================================================");
  AcX = mpu6050.getAccX();
  Serial.print("accX : ");Serial.print(AcX);
  AcY = mpu6050.getAccY();
  Serial.print("\taccY : ");Serial.print(AcY);
  AcZ = mpu6050.getAccZ();
  Serial.print("\taccZ : ");Serial.println(AcZ);
  GyX = mpu6050.getGyroX();
  Serial.print("gyroX : ");Serial.print(GyX);
  GyY = mpu6050.getGyroY();
  Serial.print("\tgyroY : ");Serial.print(GyY);
  GyZ = mpu6050.getGyroZ();    
  Serial.print("\tgyroZ : ");Serial.println(GyZ);
  Serial.println("=======================================================");
}

void connectWifi()
{
    Serial.print("Conectando-se na rede: ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.print("Conectado com sucesso na rede: ");
    Serial.println(ssid);
    Serial.print("IP obtido: ");
    Serial.println(WiFi.localIP()); 
}

void connectMQTT()
{
  if(reconecta < millis()){ //Executa a solicitacao de conexao a cada 3 segundos
    Serial.println("");
    Serial.println("Conectando ao servidor MQTT...");
    //Solicita a conexao com o servidor utilizando os parametros "mqtt_ClientID", "mqtt_user" e "mqtt_pass" 
    if(!MQTT.connect(mqtt_ClientID, mqtt_user, mqtt_pass)){
      delay(200);
      Serial.println("Falha na conexao com o servidor.");
    } 
    else {
      Serial.println("Conectado!");
      Serial.print("Enviando publicacoes para o tópico");
      Serial.println(mqtt_pub_Topic);
    }
    reconecta = millis() + 3000; //Atualiza a contagem de tempo
  }
}

void publishMPUData(){
  //Realiza a leitura do acelerômetro e giroscópio do sensor
  getMPUData();
  DynamicJsonDocument json_accel(JSON_OBJECT_SIZE(3));
  DynamicJsonDocument json_gyro(JSON_OBJECT_SIZE(3));
  
  //Atrela ao objeto "json" as leituras do sensor com os Aliases definidos
  json_accel[ALIAS1] = AcX;
  json_accel[ALIAS2] = AcY;
  json_accel[ALIAS3] = AcZ;
  json_gyro[ALIAS4] = GyX;
  json_gyro[ALIAS5] = GyY;
  json_gyro[ALIAS6] = GyZ;

  //Mede o tamanho da mensagem "json" e atrela o valor somado em uma unidade ao objeto "tamanho_payload"
  size_t tamanho_payload_accel = measureJson(json_accel) + 1;
  size_t tamanho_payload_gyro = measureJson(json_gyro) + 1;
  
  //Cria a string "payload" de acordo com o tamanho do objeto "tamanho_payload"
  char payload_accel[tamanho_payload_accel];
  char payload_gyro[tamanho_payload_gyro];

  //Copia o objeto "json" para a variavel "payload" e com o "tamanho_payload"
  serializeJson(json_accel, payload_accel, tamanho_payload_accel);
  serializeJson(json_gyro, payload_gyro, tamanho_payload_gyro);

  //Publica a variavel "payload" no servidor utilizando a variavel "mqtt_pub_Topic"
  Serial.print("Mensagem enviada: ");
  Serial.println(payload_accel);
  MQTT.publish(mqtt_pub_Topic, payload_accel);
  delay(100);
  Serial.println(payload_gyro);
  MQTT.publish(mqtt_pub_Topic, payload_gyro);
}

void loop()
{
  long now = millis();
  long last_time = 0;
  //Verifica a conexao com o servidor
  if(!MQTT.connected()){ //Se nao estiver conectado
    connectMQTT();
  }
  else {                  //Se estiver conectado
    MQTT.loop();          //Mantem a conexao ativa com o servidor
    publishMPUData();     //Envia os dados lidos via MQTT a cada 100 milissegundos
    delay(100);
  }
}
