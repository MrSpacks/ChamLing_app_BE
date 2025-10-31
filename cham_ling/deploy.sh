#!/bin/bash

# Скрипт для деплоя бэкенда на AWS Elastic Beanstalk

set -e

echo "🚀 Начинаем деплой бэкенда на AWS Elastic Beanstalk..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка наличия EB CLI
if ! command -v eb &> /dev/null; then
  echo -e "${RED}❌ Ошибка: EB CLI не установлен${NC}"
  echo "Установите: pip install awsebcli"
  exit 1
fi

# Проверка переменных окружения
if [ -z "$SECRET_KEY" ]; then
  echo -e "${YELLOW}⚠️  Предупреждение: SECRET_KEY не установлен, используйте значение по умолчанию${NC}"
fi

# Инициализация (если еще не инициализировано)
if [ ! -d ".elasticbeanstalk" ]; then
  echo -e "${GREEN}📝 Инициализация Elastic Beanstalk...${NC}"
  read -p "Введите имя приложения (по умолчанию: chamling-backend): " app_name
  app_name=${app_name:-chamling-backend}
  
  read -p "Введите регион (по умолчанию: us-east-1): " region
  region=${region:-us-east-1}
  
  eb init -p python-3.9 "$app_name" --region "$region"
fi

# Деплой
echo -e "${GREEN}☁️  Деплой на Elastic Beanstalk...${NC}"
eb deploy

echo -e "${GREEN}✅ Деплой завершен!${NC}"
echo -e "${GREEN}📋 Проверка статуса...${NC}"
eb status

echo -e "${GREEN}🎉 Готово!${NC}"

