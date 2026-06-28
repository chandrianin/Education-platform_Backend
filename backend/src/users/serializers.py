from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    # favorites = serializers.SlugRelatedField(
    #     many=True,
    #     read_only=True,
    #     slug_field='slug'
    # )

    class Meta:
        model = Profile
        fields = ['full_name', 'position', 'organization', 'photo']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            profile = instance.profile

            for attr, value in profile_data.items():
                setattr(profile, attr, value)

            profile.save()

        return instance


class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'full_name')

    def create(self, validated_data):
        profile_data = {
            'full_name': validated_data.pop('full_name'),
        }

        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )

        profile = user.profile
        profile.full_name = profile_data['full_name']
        profile.save()

        return user
