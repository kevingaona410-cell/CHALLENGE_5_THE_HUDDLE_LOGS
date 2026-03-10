import requests
import time
import random
from datetime import datetime


SERVIDOR_URL = "http://localhost:5000/logs" # URL del servidor Flask

TOKEN = {"token_service_a": "service_a", "token_service_b": "service_b"}    # Tokens válidos para autenticar los servicios que envían logs

SEVERITIES = ["INFO", "DEBUG", "WARNING", "ERROR"]   # Niveles de severidad para los logs

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

while True:
    log = {"timestamp": datetime.utcnow().isoformat(),
           "service_": "service_a",
           "severity": random.choice(SEVERITIES),
           "message": random.choice(MESSAGES)}
    headers = {
        "Authorization": f"Token{TOKEN}",
        "Content-Type": "application/json"}
    try:
        respuesta = requests.post(
            SERVIDOR_URL,
            json = log,
            headers= headers)
        
    except Exception as e: 
        print("Erro enviando log", e)
        
        time.sleep(2)
        
