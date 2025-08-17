# Gunicorn configuration for production

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = 4  # (2 x CPU cores) + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "rocktea_mall"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/rocktea.pid"
user = "ubuntu"
group = "www-data"
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn level)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Preload application for better memory usage
preload_app = True

# Restart workers after this many requests (helps with memory leaks)
max_requests = 1000
max_requests_jitter = 100

# Timeout for graceful workers restart
graceful_timeout = 30