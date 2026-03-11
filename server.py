from flask import Flask, request, jsonify      # importamos flask para crear el servidor de logging
import sqlite3
from datetime import datetime

app = Flask(__name__)        # creamos una instancia de la clase Flask para nuestro servidor 

# Definimos tokens validos para autenticar los servicios que envían logs, 1 token es invalido
TOKENS_VALIDOS = {
    "token_service_a": "service_a",
    "token_service_b": "service_b",
    "token_service_c": "service_c"}

def borrar_db():
    conn = sqlite3.connect("logs.db")     # Conectamos a la base de datos SQLite (o la creamos si no existe)
    cursor = conn.cursor()
    
    # Borramos la tabla de logs si existe
    cursor.execute("DROP TABLE IF EXISTS logs")
    
    conn.commit()   # Guardamos los cambios en la base de datos
    conn.close()    # Cerramos la conexión a la base de datos
    
borrar_db()

def iniciar_db():
    conn = sqlite3.connect("logs.db")     # Conectamos a la base de datos SQLite (o la creamos si no existe)
    cursor = conn.cursor()
    
    # Creamos la tabla de logs si no existe
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS logs (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp TEXT,
                       received_at TEXT,
                       service TEXT,
                       severity TEXT,
                       message TEXT)""")
    
    conn.commit()   # Guardamos los cambios en la base de datos
    conn.close()    # Cerramos la conexión a la base de datos

# Decorador para autenticar los servicios que envían logs
@app.route("/logs", methods=["POST"])
def recibir_logs():
    auth = request.headers.get("Authorization")             #Obtenemos el header de autorización para verificar el token
    
    # Verificamos que el header de autorización esté presente y tenga el formato correcto
    if not auth or not auth.startswith("Token "):
        return jsonify({"error": "Quién sos, bro?"}), 403   # Si no hay token, respondemos con un error 403 (Forbidden)
    
    # Extraemos el token del header de autorización
    token = auth.split(" ")[1]

    if token not in TOKENS_VALIDOS:                         # Si el token no es válido, respondemos con un error 403 (Forbidden)
        return jsonify({"error": "Quién sos, bro?"}), 403
    
    # Si el token es válido, procesamos el log recibido
    datos = request.get_json()
    print(f"[{datos['severity']}] {datos['service']} -> {datos['message']}")    
    if not datos:
        return jsonify({"error": "Json no recibido"}), 400   # Si no se reciben datos, respondemos con un error 400 (Bad Request)
    
    # Validamos campos
    campos_requeridos = ["timestamp", "service", "severity", "message"]
    
    for campo in campos_requeridos:
        if campo not in datos:
            return jsonify({"error": f"Falta el campo {campo}"}), 400  # Si falta algún campo requerido, respondemos con un error 400 (Bad Request)
        
    # Guardamos el log en la base de datos SQLite
    try:
        conn = sqlite3.connect("logs.db")
        cursor = conn.cursor()
        
        recibido_en = datetime.utcnow().isoformat()
        
        cursor.execute("""
                       INSERT INTO logs (timestamp, received_at, service, severity, message)
                       VALUES (?, ?, ?, ?, ?)""" , (
                           datos["timestamp"],
                           recibido_en,
                           datos["service"],
                           datos["severity"],
                           datos["message"]))
        conn.commit()
        conn.close() 
        return jsonify({"message": "Log recibido y guardado exitosamente"}), 200   # Si el log se guarda correctamente, respondemos con un mensaje de éxito
    except Exception as e:     
        return jsonify({"error": "Error al guardar el log"}, e), 500   # Si hay un error al guardar el log, respondemos con un error 500 (Internal Server Error)

# Endpoint para obtener logs, se pueden agregar filtros por servicio, severidad o rango de fechas
@app.route("/logs", methods=["GET"])
def obtener_logs():
    
    timestamp_inicio = request.args.get("timestamp_inicio")
    timestamp_fin = request.args.get("timestamp_fin")
    
    consulta = "SELECT * FROM logs WHERE 1=1"
    parametros = []
    
    if timestamp_inicio:
        consulta += " AND timestamp >= ?"
        parametros.append(timestamp_inicio)
    
    if timestamp_fin:
        consulta += " AND timestamp <= ?"
        parametros.append(timestamp_fin)
    
    conn = sqlite3.connect("logs.db")
    cursor= conn.cursor()
    cursor.execute(consulta, parametros)
    
    filas = cursor.fetchall()
    conn.close()
    
    logs = []
    
    for fila in filas:
        logs.append({
            "id": fila[0],
            "timestamp": fila[1],
            "received_at": fila[2],
            "service": fila[3],
            "severity": fila[4],
            "message": fila[5]})
    
    return jsonify(logs), 200   # Respondemos con la lista de logs obtenidos    
        
        
if __name__ == "__main__":
    
    iniciar_db()    
    app.run(port= 8000)