import sys
import paho.mqtt.client as mqtt
import json

# definições:
client = mqtt.Client()
broker = "10.0.0.11"
porta_broker = 1883
keep_alive_broker = 60
mqtt_sub_topic = "ESP32/MPU6050"
global count, amostragem
count = 0
amostragem = 60
arquivo_accel = open("accel_file.txt", 'w')
arquivo_accel.close()
arquivo_gyro = open("gyro_file.txt", 'w')
arquivo_gyro.close()


# Callback - conexao ao broker realizada
def on_connect(client, userdata, flags, rc):
    print("[STATUS] Conectado ao Broker. Resultado de conexao: " + str(rc))

# faz subscribe automatico no topico
client.subscribe(mqtt_sub_topic)

# Callback - mensagem recebida do broker durante certo período de tempo
def on_message(Client,userdata, msg):
    global count
    count += 1
    leitura_json = json.loads(msg.payload)

    # Salva os dados do acelerometro e giroscopio em seus respectivos arquivos
    if 'Accel' in str(leitura_json):
        arquivo_accel = open("accel_file.txt", 'a+')
        leitura_json = json.loads(msg.payload)
        arquivo_accel.write(str(leitura_json))
        arquivo_accel.write('\n')
        arquivo_accel.close()
    if 'Gyro' in str(leitura_json):
        arquivo_gyro = open("gyro_file.txt", 'a+')
        leitura_json = json.loads(msg.payload)
        arquivo_gyro.write(str(leitura_json))
        arquivo_gyro.write('\n')
        arquivo_gyro.close()

# realiza parser do arquivo de leitura dos dados para o arquivo de análise dos dados
def data_files():
    global count, amostragem
    while(count<amostragem):
        print("count: "+str(count))
        continue
    arquivo_accel = open("accel_file.txt", 'r')
    arquivo_accel_new = arquivo_accel.readlines()
    arquivo_accel.close()
    new_aquivo_accel = open("new_accel_file.txt", 'w')
    new_aquivo_accel.writelines(arquivo_accel_new)
    new_aquivo_accel.close()
    arquivo_accel = open("accel_file.txt", 'w')
    arquivo_accel.close()
    arquivo_gyro = open("gyro_file.txt", 'r')
    new_aquivo_gyro = arquivo_gyro.readlines()
    arquivo_gyro.close()
    arquivo_gyro_new = open("new_gyro_file.txt", 'w')
    arquivo_gyro_new.writelines(new_aquivo_gyro)
    arquivo_gyro_new.close()
    arquivo_gyro = open("gyro_file.txt", 'w')
    arquivo_gyro.close()
    count = 0
    return count