server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name admin.staging.rockteapl.com;

    ssl_certificate /etc/letsencrypt/live/admin.staging.rockteapl.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.staging.rockteapl.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://localhost:3006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name admin.rockteapl.com;

    ssl_certificate /etc/letsencrypt/live/admin.rockteapl.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.rockteapl.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://localhost:3005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name admin.staging.rockteapl.com admin.rockteapl.com;
    return 301 https://$host$request_uri;
}
