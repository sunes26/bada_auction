"""
Gunicorn configuration for production deployment
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
# Railway Hobby Plan: Use 2-4 workers to avoid memory/CPU limits
workers = int(os.getenv('WEB_CONCURRENCY', 2))
worker_class = 'uvicorn.workers.UvicornWorker'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'onbaek-ai-backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Debugging
reload = os.getenv('ENVIRONMENT', 'production') == 'development'
reload_engine = 'auto'

# Preload app for better performance
preload_app = True

def on_starting(server):
    """Called just before the master process is initialized."""
    print(f"[Gunicorn] Starting with {workers} workers")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("[Gunicorn] Reloading workers")

def when_ready(server):
    """Called just after the server is started."""
    print(f"[Gunicorn] Server is ready. Listening on {bind}")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"[Gunicorn] Worker spawned (pid: {worker.pid})")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"[Gunicorn] Worker exited (pid: {worker.pid})")
