"""
╔══════════════════════════════════════════════════╗
║   PENGUIN ACADEMY — SERVICIOS SIMULADOS          ║
║   Generadores de logs falsos (pero convincentes) ║
╚══════════════════════════════════════════════════╝

Simula 6 servicios distintos que envían logs al servidor central.
Cada servicio tiene su personalidad, sus errores favoritos y su token.

Modos:
  - Modo ráfaga: envía N logs de golpe
  - Modo continuo: envía logs cada X segundos con threading (BONUS)
"""

import json
import random
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE SERVICIOS
# ─────────────────────────────────────────────

SERVER_URL = "http://localhost:8080"

# Cada servicio tiene: nombre, token, y mensajes temáticos para cada severidad
SERVICES = {
    "auth-service": {
        "token": "tok_auth_x9k2mNpQ3rL",
        "logs": {
            "INFO":     ["Usuario autenticado exitosamente", "Token JWT generado", "Sesión iniciada para user_id=4821", "Refresh de token completado"],
            "DEBUG":    ["Validando claims del JWT", "Comprobando expiración de sesión", "Cache de permisos consultado", "bcrypt rounds=12"],
            "WARNING":  ["3 intentos fallidos de login para user=admin", "Token próximo a expirar en 5 min", "IP sospechosa detectada: 185.220.101.x"],
            "ERROR":    ["Fallo en conexión con OAuth provider", "JWT firmado con clave inválida", "Base de datos de sesiones no responde"],
            "CRITICAL": ["¡BRUTE FORCE DETECTADO! 1000 intentos en 60s", "Clave de firma JWT comprometida"],
        }
    },
    "payment-service": {
        "token": "tok_pay_j7vW5sBtY1eU",
        "logs": {
            "INFO":     ["Pago procesado exitosamente: $42.00", "Webhook de Stripe recibido", "Reembolso emitido para order_id=9921", "Factura generada para cliente premium"],
            "DEBUG":    ["Consultando estado de transacción", "Retry #2 a Stripe API", "Calculando impuestos para región AR"],
            "WARNING":  ["Timeout en respuesta de gateway (2.8s)", "Tarjeta rechazada, notificando usuario", "Saldo insuficiente en cuenta merchant"],
            "ERROR":    ["¡Doble cobro detectado! Transacción duplicada", "Stripe API retornó 500", "Falló el rollback de pago"],
            "CRITICAL": ["¡FRAUDE DETECTADO! Transacción bloqueada $9999", "Conexión con banco cortada durante transferencia"],
        }
    },
    "recommendation-ai": {
        "token": "tok_rec_aI4zXqD6hKnM",
        "logs": {
            "INFO":     ["Modelo v3.2 cargado en memoria", "Predicciones generadas para 150 usuarios", "A/B test iniciado: modelo_viejo vs modelo_nuevo"],
            "DEBUG":    ["Embedding calculado para item_id=7734", "Similarity score: 0.9421 entre user_42 e item_88", "Cache hit ratio: 87%"],
            "WARNING":  ["Cold start para nuevo usuario, usando heurísticas", "Dataset desactualizado (2 días sin refresh)", "GPU al 94% de capacidad"],
            "ERROR":    ["Modelo no convergió después de 1000 epochs", "NaN en capa de atención del transformer", "CUDA out of memory (requiere 14GB, hay 8GB)"],
            "CRITICAL": ["¡El modelo está recomendando lo mismo a todos! (colapso de diversidad)", "Datos de entrenamiento corruptos detectados"],
        }
    },
    "user-service": {
        "token": "tok_usr_cF8pR2wT0gVj",
        "logs": {
            "INFO":     ["Nuevo usuario registrado: johndoe_42", "Perfil actualizado para user_id=1337", "Email de bienvenida enviado", "Usuario eliminó su cuenta (bye forever)"],
            "DEBUG":    ["Consultando tabla users con JOIN profile", "Paginación: página 3, offset=60", "Validando formato de email"],
            "WARNING":  ["Usuario inactivo hace 90 días", "Email de verificación reenviado por 3ra vez", "Avatar demasiado grande (4.2MB, max 2MB)"],
            "ERROR":    ["Email duplicado en registro: ya_existe@mail.com", "Fallo al enviar email (SMTP timeout)", "Constraint violation en tabla users"],
            "CRITICAL": ["¡FUGA DE DATOS! user_ids expuestos en response pública", "Tabla users bloqueada por dead lock"],
        }
    },
    "meme-ranker": {
        "token": "tok_meme_bZ3yH9dO5lSe",
        "logs": {
            "INFO":     ["Meme clasificado como: dank (score=0.94)", "Ranking actualizado para 500 memes", "Nuevo meme viral detectado (shares=50k)", "Meme archivado por ser del 2016"],
            "DEBUG":    ["Procesando frame #42 del GIF", "Detectando texto con OCR: 'cuando el código compila'", "Hash perceptual calculado: d4e3f2a1b0c9"],
            "WARNING":  ["Meme potencialmente ofensivo detectado (score=0.71)", "Calidad de imagen baja (120x80px, lo mínimo es 500x500)", "Meme repetido (duplicate_of=meme_id=4421)"],
            "ERROR":    ["Fallo en clasificador de dankness", "API de tenor devolvió 429 (rate limit)", "GIF corrompido: frame 7 de 10 inválido"],
            "CRITICAL": ["¡El sistema rankeó un meme de política! Apaguen todo", "Loop infinito en procesamiento de GIF animado"],
        }
    },
    "penguin-monitor": {
        "token": "tok_mon_qE6uN1xA4fBr",
        "logs": {
            "INFO":     ["Health check OK: todos los servicios up", "Métricas exportadas a Prometheus", "Alert resuelto automáticamente", "Backup completado: 2.3GB en 45s"],
            "DEBUG":    ["CPU: 34%, RAM: 67%, Disk: 42%", "Latencia promedio: 12ms (p99=87ms)", "GC pause detectado: 23ms en JVM"],
            "WARNING":  ["RAM al 82% en prod-server-02", "Respuesta lenta: /api/feed tardó 3.2s", "Certificado SSL expira en 14 días"],
            "ERROR":    ["prod-server-03 no responde al health check", "Disco al 97% en nodo de logs", "Alerta de PagerDuty no entregada (webhook failed)"],
            "CRITICAL": ["¡PROD DOWN! 3 nodos sin responder", "¡CASCADING FAILURE! auth → payment → recommendation caídos"],
        }
    }
}

# Distribución de severidades (sesgada hacia INFO/DEBUG como en vida real)
SEVERITY_WEIGHTS = {
    "INFO":     40,
    "DEBUG":    30,
    "WARNING":  15,
    "ERROR":    12,
    "CRITICAL": 3,
}

# ─────────────────────────────────────────────
# GENERADOR DE LOGS
# ─────────────────────────────────────────────

def weighted_choice(weights_dict):
    """Elige una key al azar usando los pesos definidos."""
    keys = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]

def generate_log(service_name, offset_seconds=0):
    """
    Genera un log falso pero convincente para el servicio dado.
    offset_seconds permite crear logs con timestamps en el pasado (para demos).
    """
    service_config = SERVICES[service_name]
    severity = weighted_choice(SEVERITY_WEIGHTS)
    messages = service_config["logs"][severity]
    message = random.choice(messages)

    # Timestamp con posible offset para variedad en demos
    ts = datetime.now(timezone.utc) - timedelta(seconds=offset_seconds)

    return {
        "timestamp": ts.isoformat(),
        "service": service_name,
        "severity": severity,
        "message": message
    }

# ─────────────────────────────────────────────
# CLIENTE HTTP
# ─────────────────────────────────────────────

def send_logs(service_name, logs):
    """
    Envía uno o más logs al servidor central.
    Incluye el token en el header Authorization.
    Retorna (success, status_code, response_body).
    """
    token = SERVICES[service_name]["token"]
    url = f"{SERVER_URL}/logs"

    # Si es un solo log, lo enviamos como objeto; si son varios, como array
    payload = logs[0] if len(logs) == 1 else logs
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Token {token}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            resp_body = json.loads(response.read().decode("utf-8"))
            return True, response.status, resp_body
    except urllib.error.HTTPError as e:
        resp_body = json.loads(e.read().decode("utf-8"))
        return False, e.code, resp_body
    except urllib.error.URLError as e:
        return False, 0, {"error": str(e.reason)}

def send_log_single(service_name, offset_seconds=0):
    """Genera y envía un único log."""
    log = generate_log(service_name, offset_seconds)
    success, status, resp = send_logs(service_name, [log])

    icon = "✅" if success else "❌"
    print(f"  {icon} [{service_name}] [{log['severity']}] {log['message'][:60]}... → HTTP {status}")
    return success

def send_log_batch(service_name, count, spread_seconds=3600):
    """Genera y envía un lote de logs con timestamps distribuidos en el tiempo."""
    logs = [
        generate_log(service_name, offset_seconds=random.randint(0, spread_seconds))
        for _ in range(count)
    ]
    success, status, resp = send_logs(service_name, logs)
    icon = "✅" if success else "❌"
    print(f"  {icon} [{service_name}] Batch de {count} logs → HTTP {status} | Insertados: {resp.get('inserted', '?')}")
    return success

# ─────────────────────────────────────────────
# MODO CONTINUO (BONUS - Threading)
# ─────────────────────────────────────────────

_continuous_threads = []
_stop_event = threading.Event()

def _service_worker(service_name, interval_seconds):
    """
    Worker que corre en background enviando logs periódicamente.
    Se detiene cuando se dispara _stop_event.
    """
    print(f"  🔁 [{service_name}] Iniciando envío continuo cada {interval_seconds}s")
    while not _stop_event.is_set():
        log = generate_log(service_name)
        success, status, _ = send_logs(service_name, [log])
        icon = "✅" if success else "❌"
        print(f"  {icon} [{service_name}] [{log['severity']}] {log['message'][:50]}...")
        _stop_event.wait(timeout=interval_seconds)  # Espera interrumpible
    print(f"  ⏹ [{service_name}] Worker detenido")

def start_continuous_mode(services_intervals=None):
    """
    Inicia todos los servicios en modo continuo con threading.
    services_intervals: dict de {service_name: interval_seconds}
    Por defecto, todos los servicios con intervalos aleatorios.
    """
    global _continuous_threads
    _stop_event.clear()

    if services_intervals is None:
        # Cada servicio con un intervalo distinto para simular actividad real
        services_intervals = {
            "auth-service":       3,
            "payment-service":    5,
            "recommendation-ai":  4,
            "user-service":       6,
            "meme-ranker":        2,
            "penguin-monitor":    8,
        }

    print(f"\n{'='*60}")
    print("  MODO CONTINUO ACTIVADO — Ctrl+C para detener")
    print(f"{'='*60}")

    _continuous_threads = []
    for service_name, interval in services_intervals.items():
        t = threading.Thread(
            target=_service_worker,
            args=(service_name, interval),
            daemon=True,
            name=f"worker-{service_name}"
        )
        t.start()
        _continuous_threads.append(t)

    return _continuous_threads

def stop_continuous_mode():
    """Detiene todos los workers del modo continuo."""
    _stop_event.set()
    for t in _continuous_threads:
        t.join(timeout=5)
    print("  Todos los workers detenidos.")

# ─────────────────────────────────────────────
# DEMOSTRACIÓN DE TOKEN INVÁLIDO
# ─────────────────────────────────────────────

def demo_invalid_token():
    """Muestra qué pasa cuando alguien intenta colar un log sin token válido."""
    print("\n  [TEST] Intentando enviar log con token inválido...")
    url = f"{SERVER_URL}/logs"
    body = json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "hacker-service",
        "severity": "INFO",
        "message": "Definitivamente no soy un intruso"
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Token tok_fake_NOSOYBRO123"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"  ⚠️  Inesperadamente aceptado: {response.status}")
    except urllib.error.HTTPError as e:
        resp = json.loads(e.read().decode("utf-8"))
        print(f"  ✅ Rechazado correctamente: HTTP {e.code} → {resp}")

# ─────────────────────────────────────────────
# MAIN — Modo ráfaga por defecto
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("╔══════════════════════════════════════════════════╗")
    print("║   PENGUIN ACADEMY — CLIENTES DE LOGGING          ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    mode = sys.argv[1] if len(sys.argv) > 1 else "burst"

    if mode == "continuous":
        # Modo continuo con threads (BONUS)
        threads = start_continuous_mode()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n[CLIENTS] Deteniendo workers...")
            stop_continuous_mode()

    else:
        # ── Modo ráfaga ──────────────────────────────────────────────
        print("📤 FASE 1: Enviando logs individuales de cada servicio")
        print("-" * 55)
        for service in SERVICES:
            send_log_single(service, offset_seconds=random.randint(0, 7200))

        print()
        print("📦 FASE 2: Enviando batches de logs (carga alta)")
        print("-" * 55)
        for service in SERVICES:
            batch_size = random.randint(5, 15)
            send_log_batch(service, batch_size)

        print()
        print("🔒 FASE 3: Probando seguridad (token inválido)")
        print("-" * 55)
        demo_invalid_token()

        print()
        print("📊 FASE 4: Consultando stats del servidor")
        print("-" * 55)
        try:
            with urllib.request.urlopen(f"{SERVER_URL}/stats", timeout=5) as r:
                stats = json.loads(r.read().decode("utf-8"))
                print(f"  Total logs en DB: {stats['total_logs']}")
                print("  Por servicio:")
                for s in stats["by_service"]:
                    print(f"    • {s['service']}: {s['count']} logs")
                print("  Por severidad:")
                for s in stats["by_severity"]:
                    print(f"    • {s['severity']}: {s['count']} logs")
        except Exception as e:
            print(f"  ❌ Error consultando stats: {e}")

        print()
        print("✅ Demo completada. Ejecutá con 'python clients.py continuous' para modo continuo.")