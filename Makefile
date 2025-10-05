.PHONY: run

run:
	@echo "Активирую виртуальное окружение..."
	@source .venv/bin/activate
	@echo "Перехожу в директорию cham_ling..."
	@cd cham_ling
	@echo "Запускаю Django сервер..."
	@python manage.py runserver

clean:
	@echo "Остановка сервера и очистка (если нужно)..."
	@pkill -f runserver || true
	@deactivate || true
	@echo "Готово!"
