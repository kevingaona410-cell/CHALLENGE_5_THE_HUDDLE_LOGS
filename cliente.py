import requests
import time
import random
from datetime import datetime

SERVIDOR_URL = "http://localhost:8000/logs" # URL del servidor Flask

TOKEN = {"token_service_a": "service_a" , "token_service_b" : "service_b" , "token_service_c" :"service_c" , "token_service_fake" : "service_fake"}       # Tokens válidos para autenticar los servicios que envían logs
SEVERITIES = ["INFO", "DEBUG", "WARNING", "ERROR"]   # Niveles de severidad para los logs

# Mensajes de log para simular diferentes eventos en el sistema
MESSAGES = ["operation completed successfully",
    "request processed",
    "resource accessed",
    "unexpected condition detected",
    "temporary failure occurred",
    "connection established",
    "connection closed",
    "data processed",
    "retrying operation",
    "internal check executed"]

# Simulamos el envío de logs desde un servicio cliente hacia el servidor Flask
while True:
    token_seleccionado = random.choice(list(TOKEN))          # seleccion aleatoria del token para ver 1 valido y un invalido
    log = {"timestamp": datetime.utcnow().isoformat(), # Timestamp actual en formato ISO 8601
           "service": token_seleccionado,                      # Nombre del servicio que envía el log
           "severity": random.choice(SEVERITIES),      # Nivel de severidad aleatorio para el log
           "message": random.choice(MESSAGES)}         # Mensaje de log aleatorio para simular diferentes eventos en el sistema


    # Headers para la autenticación del servicio cliente con el servidor Flask
    headers = {
        "Authorization": f"Token {token_seleccionado}",
        "Content-Type": "application/json"}
    
    try:            # Enviamos el log al servidor Flask utilizando una solicitud POST con el log en formato JSON y los headers de autenticación
        respuesta = requests.post(
            SERVIDOR_URL,
            json = log,
            headers= headers)
        print(respuesta.status_code, respuesta.json())

# Si la respuesta del servidor no es 200 (OK), imprimimos un mensaje de error con el código de estado y el contenido de la respuesta        
    except Exception as e:
        print("Error enviando log", e)        
        time.sleep(0.5)
        
