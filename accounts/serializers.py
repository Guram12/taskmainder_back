from rest_framework import serializers
from .models import CustomUser
from django.conf import settings



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password', 'phone_number', 'profile_picture')

    def create(self, validated_data):
        profile_picture = validated_data.get('profile_picture', settings.DEFAULT_PROFILE_PICTURE_URL)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            profile_picture=profile_picture,
            phone_number=validated_data.get('phone_number', '')
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'phone_number', 'profile_picture')













































