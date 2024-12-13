import sys
from leitura import *
import math
import json
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, porta_broker, keep_alive_broker)
client.loop_start()

# Definição de variáveis globais
global delta_a_ref, delta_w_ref
global AUFT_brusca, AUFT_suave, WUFT
global amostragem

amostragem = 60
delta_a_ref = 0.725
delta_w_ref = 16.55
AUFT_brusca = 2.2
AUFT_suave = 1.6
WUFT = 220

mqtt_pub_topic_accel = "raspberry/acelerometro"
mqtt_pub_topic_gyro = "raspberry/giroscopio"

def parser_json_from_files():
    accel_json_list = []
    gyro_json_list = []

    with open("new_accel_file.txt", 'r') as accel_file:
        a_file = accel_file.readlines()
        for i in a_file:
            i = i.replace("'", '"')
            obj = json.loads(i)
            accel_json_list.append(obj)

    with open("new_gyro_file.txt", 'r') as gyro_file:
        g_file = gyro_file.readlines()
        for i in g_file:
            i = i.replace("'", '"')
            obj = json.loads(i)
            gyro_json_list.append(obj)

    return [accel_json_list,gyro_json_list]

# calcula valor resultante dos componentes do acelerometro e giroscopio para cada intervalo
def calculate_result_values():
    accel_result_list = []
    gyro_result_list = []

    json_list = parser_json_from_files()
    accel_json_list = json_list[0]
    gyro_json_list = json_list[1]

    # acelerômetro:
    for i in range(0,int(len(accel_json_list))):
        a_result = math.sqrt((accel_json_list[i]['AccelX'])**2 + (accel_json_list[i]['AccelY'])**2 + (accel_json_list[i]['AccelZ'])**2) 
        accel_result_list.append(a_result)
        mqtt_msg_accel = json.dumps({"accel":a_result})
        client.publish(mqtt_pub_topic_accel, mqtt_msg_accel)

    # giroscópio:
    for i in range(0,int(len(gyro_json_list))):
        g_result = math.sqrt((gyro_json_list[i]['GyroX'])**2 + (gyro_json_list[i]['GyroY'])**2 + (gyro_json_list[i]['GyroZ'])**2)
        gyro_result_list.append(g_result)
        mqtt_msg_gyro = json.dumps({"gyro":g_result})
        client.publish(mqtt_pub_topic_gyro, mqtt_msg_gyro)

    return [accel_result_list, gyro_result_list]

# seleciona valores máximo e mínimo dos vetores resultantes
def calculate_max_min_values():
    result_values_list = calculate_result_values()
    accel_result_list = result_values_list[0]
    gyro_result_list = result_values_list[1]

    A_max = max(accel_result_list)
    A_min = min(accel_result_list)
    W_max = max(gyro_result_list)
    W_min = min(gyro_result_list)

    # calcula diferença entre os valores máximo e mínimos
    delta_a = A_max-A_min
    delta_w = W_max-W_min
    return [accel_result_list, gyro_result_list, A_max,A_min,W_max,W_min,delta_a,delta_w]

def calculate_med_dif_for_moviment():
    global amostragem
    max_min_values = calculate_max_min_values()
    accel_result_list = max_min_values[0]
    gyro_result_list = max_min_values[1]
    A_max = max_min_values[2]
    W_max = max_min_values[4]

    a_mov_list = []
    w_mov_list = []

    # para identificar o movimento com acelerometro
    for i in range(0,int(len(accel_result_list))):
        a_mov = A_max - accel_result_list[i]
        a_mov_list.append(a_mov)
        a_mov_media = sum(a_mov_list)/(amostragem/2)

    for i in range(0,int(len(gyro_result_list))):
        w_mov = W_max - gyro_result_list[i]
        w_mov_list.append(w_mov)
        w_mov_media = sum(w_mov_list)/(amostragem/2)

    return [a_mov_media,w_mov_media]

def calculate_Accel_med():
    json_list = parser_json_from_files()
    accel_json_list = json_list[0]
    gyro_json_list = json_list[1]

    global amostragem
    ax_list = []
    ay_list = []
    az_list = []

    for i in range(0,int(len(accel_json_list))):
        ax = (accel_json_list[i]['AccelX'])
        ax_list.append(ax)
        ay = (accel_json_list[i]['AccelY'])
        ay_list.append(ay)
        az = (accel_json_list[i]['AccelZ'])
        az_list.append(az)

    Ax_medio = sum(ax_list)/(amostragem/2)
    Ay_medio = sum(ay_list)/(amostragem/2)
    Az_medio = sum(az_list)/(amostragem/2)

    return [Ax_medio,Ay_medio,Az_medio]

# verifica se está em movimento ou parado:
# 1) verificação do valor do giroscópio
# 2) verificação do valor do acelerometro

def analyze_status():
    global delta_a_ref, delta_w_ref
    deltas = calculate_max_min_values()
    delta_a = deltas[6]
    delta_w = deltas[7]

    if delta_w < delta_w_ref:
        if delta_a < delta_a_ref:
            status = 'parado'
        else:
            status = 'em movimento'
    else:
        status = 'em movimento'
    return status

def analyze_position():
    global AUFT_brusca, AUFT_suave, WUFT
    status = analyze_status()

    mov_medias = calculate_med_dif_for_moviment()
    a_mov_media = mov_medias[0]
    w_mov_media = mov_medias[1]

    a_medias = calculate_Accel_med()
    Ax_medio = a_medias[0]
    Ay_medio = a_medias[1]
    Az_medio = a_medias[2]

    maximos = calculate_max_min_values()
    A_max = maximos[2]
    W_max = maximos[4]

    # se está parado, verifica qual a posição
    if status == 'parado':
        if Ax_medio > Ay_medio:
            if Ax_medio > Az_medio:
                posicao = 'em pe'
            else:
                posicao = 'deitada'
        elif Az_medio > Ay_medio:
            if Az_medio > Ax_medio:
                posicao = 'deitada'
            else:
                posicao = 'sentada'
        else:
            posicao = 'deitada'
    elif status == 'em movimento':
        if A_max > AUFT_brusca:
            if W_max > WUFT:
                if a_mov_media < 0.3:
                    if w_mov_media < 40.0:
                        posicao = 'caiu'
                    else:
                        posicao = 'andando'
                else:
                    posicao = 'andando'
            elif (A_max < AUFT_suave) and (A_max > 1.0):
                if W_max > 95.0:
                    if a_mov_media < 0.2:
                        if w_mov_media < 20.0:
                            posicao = 'caiu'
                        else:
                            posicao = 'andando'
                    else:
                        posicao = 'andando'
                else:
                    posicao = 'andando'
            else:
                posicao = 'andando'
    elif (A_max < AUFT_suave) and (A_max > 1.0):
        if W_max > 95.0:
            if a_mov_media < 0.2:
                if w_mov_media < 20.0:
                    posicao = 'caiu'
                else:
                    posicao = 'andando'
            else:
                posicao = 'andando'
        else:
            posicao = 'andando'
    else:
        posicao = 'andando'
        
    print(posicao)
    return posicao