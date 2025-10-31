# Руководство по развертыванию Backend на AWS

## Быстрый старт

### 1. Установка EB CLI

```bash
pip install awsebcli
```

### 2. Инициализация Elastic Beanstalk

```bash
cd cham_ling_app_BE/cham_ling
eb init -p python-3.9 chamling-backend --region us-east-1
```

### 3. Создание окружения

```bash
eb create chamling-production \
  --instance-type t3.small \
  --envvars SECRET_KEY=your-secret-key-here,DEBUG=False,ALLOWED_HOSTS=*.elasticbeanstalk.com,yourdomain.com
```

### 4. Настройка переменных окружения

Через EB Console или CLI:

```bash
eb setenv \
  SECRET_KEY=your-secret-key \
  DEBUG=False \
  ALLOWED_HOSTS=yourdomain.com,*.elasticbeanstalk.com \
  CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com \
  UNSPLASH_API_KEY=your-unsplash-key
```

### 5. Подключение RDS

```bash
# Создать RDS instance
eb create chamling-rds \
  --database.engine postgres \
  --database.username chamling \
  --database.password YourSecurePassword123! \
  --database.instance db.t3.micro
```

Или создать RDS отдельно и подключить через переменные окружения:

```bash
eb setenv \
  RDS_DB_NAME=chamling \
  RDS_USERNAME=chamling \
  RDS_PASSWORD=YourSecurePassword123! \
  RDS_HOSTNAME=your-rds-endpoint.rds.amazonaws.com \
  RDS_PORT=5432
```

### 6. Деплой

```bash
eb deploy
```

### 7. Выполнение миграций

```bash
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py migrate
python manage.py createsuperuser
exit
```

## Переменные окружения

Обязательные:
- `SECRET_KEY` - секретный ключ Django
- `DEBUG` - False для продакшена
- `ALLOWED_HOSTS` - разрешенные хосты

Для RDS:
- `RDS_DB_NAME` - имя базы данных
- `RDS_USERNAME` - пользователь БД
- `RDS_PASSWORD` - пароль БД
- `RDS_HOSTNAME` - хост RDS
- `RDS_PORT` - порт (обычно 5432)

Для CORS:
- `CORS_ALLOWED_ORIGINS` - список разрешенных доменов через запятую

Опциональные:
- `UNSPLASH_API_KEY` - ключ API Unsplash

## Просмотр логов

```bash
eb logs
```

## Мониторинг

```bash
eb health
eb status
```

