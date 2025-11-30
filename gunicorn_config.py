"""
Configuración de Gunicorn para Render
Optimizado para evitar timeouts con envío de correos asíncronos
"""
import multiprocessing
import os

# Bind
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Workers
workers = int(os.environ.get('WEB_CONCURRENCY', 2))
worker_class = 'sync'  # Usamos sync porque el threading lo manejamos en Python
# threads no se usa con worker_class='sync', se ignora automáticamente

# Timeout optimizado para emails críticos (verificación de cuenta)
# 45 segundos es suficiente para envío síncrono de emails con SendGrid
timeout = 45
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Worker timeout
graceful_timeout = 30

# Preload app (mejora el tiempo de inicio)
preload_app = True

# Max requests (para evitar memory leaks)
max_requests = 1000
max_requests_jitter = 50

