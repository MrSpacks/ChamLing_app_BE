from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Dictionary
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает тестовые английско-русские словари для продажи от случайных пользователей'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Количество словарей для создания (по умолчанию 5)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Получаем всех пользователей
        users = User.objects.all()
        
        if not users.exists():
            self.stdout.write(
                self.style.ERROR('Нет пользователей в базе данных. Сначала создайте пользователей.')
            )
            return
        
        # Названия и описания словарей
        dictionaries_data = [
            {
                'name': 'Английский для начинающих',
                'description': 'Основные слова и фразы для изучения английского языка с нуля',
            },
            {
                'name': 'Бизнес английский',
                'description': 'Специализированный словарь для делового общения на английском',
            },
            {
                'name': 'Английский для путешествий',
                'description': 'Полезные слова и фразы для туристов и путешественников',
            },
            {
                'name': 'Английские идиомы и выражения',
                'description': 'Популярные идиомы, фразовые глаголы и устойчивые выражения',
            },
            {
                'name': 'Английский для детей',
                'description': 'Яркий и интересный словарь для изучения английского детьми',
            },
            {
                'name': 'Технический английский',
                'description': 'Словарь для IT-специалистов и программистов',
            },
            {
                'name': 'Медицинский английский',
                'description': 'Специализированная лексика для медиков и студентов-медиков',
            },
            {
                'name': 'Английский для экзаменов',
                'description': 'Подготовка к IELTS, TOEFL и другим международным экзаменам',
            },
        ]
        
        created_count = 0
        
        for i in range(count):
            # Выбираем случайного пользователя
            owner = random.choice(users)
            
            # Выбираем случайные данные словаря
            dict_data = random.choice(dictionaries_data)
            
            # Генерируем случайную цену от 0.50 до 10.00
            price = round(random.uniform(0.5, 10.0), 2)
            
            # Создаем словарь
            dictionary = Dictionary.objects.create(
                owner=owner,
                name=f"{dict_data['name']} {i+1}",
                description=dict_data['description'],
                source_lang='en',
                target_lang='ru',
                price=price,
                is_for_sale=True,
                allow_temporary_access=random.choice([True, False]),
                temporary_days=random.choice([7, 14, 30]) if random.choice([True, False]) else None,
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Создан словарь "{dictionary.name}" для пользователя {owner.username} '
                    f'(цена: ${price})'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Успешно создано {created_count} тестовых словарей!'
            )
        )

