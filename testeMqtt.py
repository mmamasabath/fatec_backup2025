import paho.mqtt.client as mqtt
import threading

# Função de retorno de chamada quando o cliente se conecta ao broker
def on_connect(client, userdata, flags, rc):
    print("Conectado com código de resultado: {}".format(rc))
    # Inscrever-se no tópico
    client.subscribe("test/topic")

# Função de retorno de chamada quando uma mensagem é recebida
def on_message(client, userdata, msg):
    print("Recebido '{}' no tópico '{}'".format(msg.payload.decode(), msg.topic))

# Criar um cliente MQTT
client = mqtt.Client()

# Definir as funções de retorno de chamada
client.on_connect = on_connect
client.on_message = on_message

# Conectar ao broker
client.connect("localhost", 1883, 60)

# Iniciar o loop de rede em um thread separado
client.loop_start()

# Loop para enviar mensagens no terminal
try:
    while True:
        mensagem = input("Digite a mensagem para publicar (ou 'sair' para encerrar): ")
        if mensagem.lower() == 'sair':
            break
        client.publish("test/topic", mensagem)
except KeyboardInterrupt:
    pass
finally:
    client.loop_stop()  # Parar o loop quando terminar
    client.disconnect()  # Desconectar do broker
