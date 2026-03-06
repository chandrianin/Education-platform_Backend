import os

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Category, LibraryFile


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


def get_file_type_by_extension(filename):
    FILE_TYPE_EXTENSIONS = {
        'document': ['.pdf', '.doc', '.docx', '.odt', '.ppt', '.pptx'],
        'image': ['.jpg', '.jpeg', '.png'],
        'video': ['.mp4'],
    }

    ext = os.path.splitext(filename)[1].lower()

    for file_type, extensions in FILE_TYPE_EXTENSIONS.items():
        if ext in extensions:
            return file_type

    raise ValidationError('Неподдерживаемый формат файла.')

class LibraryFileSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    category_details = CategorySerializer(source='categories', many=True, read_only=True)

    def validate(self, data):
        file = data.get('file')

        if file:
            data['file_type'] = get_file_type_by_extension(file.name)

        return data
    class Meta:
        model = LibraryFile
        fields = [
            'slug', 'title', 'description',
            'file_type', 'file', 'category_details',
            'author_name', 'created_at'
        ]
        read_only_fields = ['slug', 'author_name', 'created_at', "file_type"]
