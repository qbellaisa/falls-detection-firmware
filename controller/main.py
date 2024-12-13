import sys
import cv2
from leitura import *
from analise import *

mqtt_pub_topic_position = "raspberry/posicao"
print("[STATUS] Inicializando MQTT...")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, porta_broker, keep_alive_broker)
client.loop_start()

while(True):
    count_leitura = data_files()
    if count_leitura == 0:
        posicao = analyze_position()
        mqtt_msg_position = json.dumps({"posicao":posicao})
        client.publish(mqtt_pub_topic_position, mqtt_msg_position)