from rest_framework import serializers
from .models import ModuleItem, Module, ModuleCompletion
from library.serializers import LibraryFileSerializer


class ModuleItemSerializer(serializers.ModelSerializer):
    library_file = LibraryFileSerializer(read_only=True)

    class Meta:
        model = ModuleItem
        fields = ['id', 'type', 'text', 'library_file', 'order']


class ModuleSerializer(serializers.ModelSerializer):
    items = ModuleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'type', 'order', 'items']


class ModuleCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleCompletion
        fields = ['module', 'completed']

