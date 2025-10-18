# Makefile для запуска Django проекта ChamLing

# Активация виртуального окружения и запуск сервера
run:
	source venv/bin/activate && cd cham_ling && python manage.py runserver

# Альтернатива для Windows (если нужно)
run-win:
	call venv\Scripts\activate && cd cham_ling && python manage.py runserver