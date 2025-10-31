from django.core.management.base import BaseCommand
from api.models import Dictionary, Word
import random

class Command(BaseCommand):
    help = 'Добавляет слова к существующим словарям'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Количество слов на словарь (по умолчанию 10)',
        )

    def handle(self, *args, **options):
        words_per_dict = options['count']
        
        # Получаем все словари
        dictionaries = Dictionary.objects.all()
        
        if not dictionaries.exists():
            self.stdout.write(
                self.style.ERROR('Нет словарей в базе данных.')
            )
            return
        
        # Примеры английско-русских слов для добавления
        english_words = [
            {'word': 'hello', 'translation': 'привет', 'example': 'Hello, how are you?'},
            {'word': 'world', 'translation': 'мир', 'example': 'The world is beautiful'},
            {'word': 'book', 'translation': 'книга', 'example': 'I love reading books'},
            {'word': 'water', 'translation': 'вода', 'example': 'Please give me some water'},
            {'word': 'friend', 'translation': 'друг', 'example': 'He is my best friend'},
            {'word': 'house', 'translation': 'дом', 'example': 'I live in a big house'},
            {'word': 'sun', 'translation': 'солнце', 'example': 'The sun is shining'},
            {'word': 'moon', 'translation': 'луна', 'example': 'The moon is full tonight'},
            {'word': 'star', 'translation': 'звезда', 'example': 'Look at that bright star'},
            {'word': 'dog', 'translation': 'собака', 'example': 'My dog is very friendly'},
            {'word': 'cat', 'translation': 'кот', 'example': 'The cat is sleeping'},
            {'word': 'car', 'translation': 'машина', 'example': 'I drive a red car'},
            {'word': 'tree', 'translation': 'дерево', 'example': 'The tree is very tall'},
            {'word': 'flower', 'translation': 'цветок', 'example': 'Beautiful flowers bloom in spring'},
            {'word': 'bird', 'translation': 'птица', 'example': 'The bird is flying'},
            {'word': 'computer', 'translation': 'компьютер', 'example': 'I work on my computer'},
            {'word': 'phone', 'translation': 'телефон', 'example': 'My phone is ringing'},
            {'word': 'music', 'translation': 'музыка', 'example': 'I love listening to music'},
            {'word': 'food', 'translation': 'еда', 'example': 'The food is delicious'},
            {'word': 'time', 'translation': 'время', 'example': 'What time is it?'},
            {'word': 'day', 'translation': 'день', 'example': 'Have a nice day!'},
            {'word': 'night', 'translation': 'ночь', 'example': 'Good night!'},
            {'word': 'morning', 'translation': 'утро', 'example': 'Good morning!'},
            {'word': 'evening', 'translation': 'вечер', 'example': 'Good evening!'},
            {'word': 'school', 'translation': 'школа', 'example': 'I go to school every day'},
            {'word': 'teacher', 'translation': 'учитель', 'example': 'My teacher is very kind'},
            {'word': 'student', 'translation': 'студент', 'example': 'I am a student'},
            {'word': 'learn', 'translation': 'учить', 'example': 'I learn English'},
            {'word': 'study', 'translation': 'изучать', 'example': 'I study hard'},
            {'word': 'read', 'translation': 'читать', 'example': 'I like to read books'},
            {'word': 'write', 'translation': 'писать', 'example': 'I write in my diary'},
            {'word': 'speak', 'translation': 'говорить', 'example': 'I speak English'},
            {'word': 'listen', 'translation': 'слушать', 'example': 'Listen to me carefully'},
            {'word': 'see', 'translation': 'видеть', 'example': 'I can see the mountains'},
            {'word': 'hear', 'translation': 'слышать', 'example': 'I hear music'},
            {'word': 'know', 'translation': 'знать', 'example': 'I know the answer'},
            {'word': 'think', 'translation': 'думать', 'example': 'I think it is good'},
            {'word': 'want', 'translation': 'хотеть', 'example': 'I want to learn'},
            {'word': 'need', 'translation': 'нуждаться', 'example': 'I need help'},
            {'word': 'like', 'translation': 'нравиться', 'example': 'I like pizza'},
            {'word': 'love', 'translation': 'любить', 'example': 'I love you'},
            {'word': 'happy', 'translation': 'счастливый', 'example': 'I am very happy'},
            {'word': 'sad', 'translation': 'грустный', 'example': 'Why are you sad?'},
            {'word': 'big', 'translation': 'большой', 'example': 'This is a big house'},
            {'word': 'small', 'translation': 'маленький', 'example': 'A small cat'},
            {'word': 'good', 'translation': 'хороший', 'example': 'Good job!'},
            {'word': 'bad', 'translation': 'плохой', 'example': 'This is bad news'},
            {'word': 'new', 'translation': 'новый', 'example': 'I have a new car'},
            {'word': 'old', 'translation': 'старый', 'example': 'This is an old book'},
            {'word': 'beautiful', 'translation': 'красивый', 'example': 'She is beautiful'},
        ]
        
        total_added = 0
        
        for dictionary in dictionaries:
            # Пропускаем словари, которые не английско-русские
            if dictionary.source_lang.lower() != 'en' or dictionary.target_lang.lower() != 'ru':
                continue
            
            # Получаем уже существующие слова
            existing_words = Word.objects.filter(dictionary=dictionary).values_list('word', flat=True)
            
            # Фильтруем слова, которые еще не добавлены
            available_words = [w for w in english_words if w['word'].lower() not in [ew.lower() for ew in existing_words]]
            
            # Выбираем случайные слова
            words_to_add = random.sample(available_words, min(words_per_dict, len(available_words)))
            
            added_count = 0
            for word_data in words_to_add:
                word, created = Word.objects.get_or_create(
                    dictionary=dictionary,
                    word=word_data['word'],
                    defaults={
                        'translation': word_data['translation'],
                        'example': word_data['example'],
                    }
                )
                if created:
                    added_count += 1
            
            if added_count > 0:
                total_added += added_count
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Добавлено {added_count} слов в словарь "{dictionary.name}" (ID: {dictionary.id})'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Всего добавлено {total_added} слов!'
            )
        )

