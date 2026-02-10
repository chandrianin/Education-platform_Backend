import os

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Category, LibraryFile


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


def validate_file_extension(value, file_type):
    """Валидатор для поддерживаемых расширений"""
    FILE_TYPE_EXTENSIONS = {
        'document': ['.pdf', '.doc', '.docx', '.odt', '.ppt', '.pptx'],
        'image': ['.jpg', '.jpeg', '.png'],
        'video': ['.mp4'],
    }

    ext = os.path.splitext(value.name)[1]

    valid_extensions = [ext for exts in FILE_TYPE_EXTENSIONS.values() for ext in exts]
    if ext not in valid_extensions:
        raise ValidationError('Неподдерживаемый формат файла.')

    allowed = FILE_TYPE_EXTENSIONS.get(file_type)
    if allowed and ext not in allowed:
        raise ValidationError(f"Файл с расширением {ext} не соответствует типу {file_type}.")


class LibraryFileSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    category_details = CategorySerializer(source='categories', many=True, read_only=True)

    def validate(self, data):
        file = data.get('file')
        file_type = data.get('file_type')
        if file and file_type:
            validate_file_extension(file, file_type)
        return data

    class Meta:
        model = LibraryFile
        fields = [
            'slug', 'title', 'description',
            'file_type', 'file', 'category_details',
            'author_name', 'created_at'
        ]
        read_only_fields = ['slug', 'author_name', 'created_at']
