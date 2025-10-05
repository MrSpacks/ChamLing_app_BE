# ChamLing_app_BE

# Steps for start project:

# fast start

make run

or

# not fast)

1 start venv fo python - source .venv/bin/activate
2 cd cham_ling
3 start Django server - python manage.py runserver

For add new element in model : python manage.py makemigrations
python manage.py migrate

# pull AWS sserver - git pull origin main

              sudo systemctl restart nginx

# conect AWS server

ssh -i /Users/sergeipetuhov/Downloads/myproject.pem ubuntu@13.61.13.177
ssh -i /Users/sergeipetuhov/Downloads/myproject.pem ubuntu@13.62.115.181

cd ~/QuickWeb_BE
source venv/bin/activate
gunicorn quick_web.wsgi:application --bind 0.0.0.0:8000

server {
listen 80;
server_name 13.62.115.181 webcards.click;

    # Редирект на HTTPS (если SSL настроен)
    return 301 https://$server_name$request_uri;

    # Статические файлы (опционально)
    location /static/ {
        alias /home/ubuntu/QuickWeb_BE/static/;
    }

    location /media/ {
        alias /home/ubuntu/QuickWeb_BE/media/;
    }

}

server {
listen 443 ssl;
server_name 13.62.115.181 webcards.click;

    # Самоподписанный сертификат (замени на пути из ACM, если настроено)
    ssl_certificate /etc/ssl/certs/selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/selfsigned.key;

    # Прокси к Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Статические файлы
    location /static/ {
        alias /home/ubuntu/QuickWeb_BE/static/;
    }

    location /media/ {
        alias /home/ubuntu/QuickWeb_BE/media/;
    }

}
