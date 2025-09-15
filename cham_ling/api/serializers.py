from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Dictionary, Word

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Неверные учетные данные')
        return {'user': user}

class DictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dictionary
        fields = ['id', 'owner', 'name', 'description', 'source_lang', 'target_lang', 'price', 'is_temporary_access', 'temp_duration_days', 'is_for_sale', 'cover_image']
        extra_kwargs = {
            'owner': {'read_only': True},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        return Dictionary.objects.create(owner=request.user, **validated_data)

    def validate(self, data):
        # Дополнительная валидация на API-уровне
        if data.get('is_for_sale'):
            if not data.get('name'):
                raise serializers.ValidationError("Название обязательно для словаря на продажу.")
            if not data.get('description'):
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