server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.staging.rockteapl.com;
    client_max_body_size 5M;

    ssl_certificate /etc/letsencrypt/live/api.staging.rockteapl.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.staging.rockteapl.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        alias /home/ubuntu/django-app/dev/main/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name api.staging.rockteapl.com;
    return 301 https://$host$request_uri;
}
