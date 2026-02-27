server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name dropshippers.staging.rockteapl.com;

    ssl_certificate /etc/letsencrypt/live/dropshippers.staging.rockteapl.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dropshippers.staging.rockteapl.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://localhost:3004;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name dropshippers.rockteapl.com;

    ssl_certificate /etc/letsencrypt/live/dropshippers.rockteapl.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dropshippers.rockteapl.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://localhost:3002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name dropshippers.staging.rockteapl.com dropshippers.rockteapl.com;
    return 301 https://$host$request_uri;
}
