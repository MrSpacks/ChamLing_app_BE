from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import  Dictionary, Word
from django.contrib.auth import get_user_model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError({'email': ['Invalid email or password.']})
        return {'user': user}

class DictionarySerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    word_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Dictionary
        fields = ['id', 'owner', 'name', 'description', 'source_lang', 'target_lang', 'price', 'allow_temporary_access', 'temporary_days', 'is_for_sale', 'cover_image', 'cover_image_file', 'cover_image_url', 'is_owner', 'word_count', 'created_at']
        extra_kwargs = {
            'owner': {'read_only': True},
            'cover_image_file': {'write_only': True, 'required': False},
        }
    
    def get_cover_image_url(self, obj):
        """Возвращает URL изображения (из файла или URL поля)"""
        if obj.cover_image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image_file.url)
            return obj.cover_image_file.url
        return obj.cover_image if obj.cover_image else None
    
    def get_is_owner(self, obj):
        """Проверяет является ли текущий пользователь владельцем"""
        request = self.context.get('request')
        if request and request.user:
            return obj.owner == request.user
        return False
    
    def get_word_count(self, obj):
        """Возвращает количество слов в словаре"""
        return obj.words.count()

    def create(self, validated_data):
        request = self.context.get('request')
        return Dictionary.objects.create(owner=request.user, **validated_data)
    
    def update(self, instance, validated_data):
        """Обновление словаря"""
        # Обновляем только переданные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate(self, data):
        # Дополнительная валидация на API-уровне
        if data.get('is_for_sale'):
            if not data.get('name') and not self.instance:
                raise serializers.ValidationError("Название обязательно для словаря на продажу.")
            if not data.get('description') and not self.instance:
                raise serializers.ValidationError("Описание обязательно для словаря на продажу.")
        return data

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['id', 'dictionary', 'word', 'translation', 'image_url', 'example']
        extra_kwargs = {
            'dictionary': {'read_only': True},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        dictionary_id = request.data.get('dictionary_id')
        dictionary = Dictionary.objects.get(id=dictionary_id, owner=request.user)
        validated_data['dictionary'] = dictionary
        return Word.objects.create(**validated_data)