from rest_framework import serializers
from allauth.account.utils import send_email_confirmation
from .models import CustomUser
from django.conf import settings

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password', 'phone_number', 'profile_picture', 'timezone')

    def create(self, validated_data):
        profile_picture = validated_data.pop('profile_picture', None)  # Remove profile_picture from validated_data
        if not profile_picture:  # Use default only if no profile picture is provided
            profile_picture = settings.DEFAULT_PROFILE_PICTURE_URL

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            profile_picture=profile_picture,
            timezone=validated_data.get('timezone', 'UTC'),
            phone_number=validated_data.get('phone_number', '')
        )
        send_email_confirmation(self.context['request'], user)
        print(f"User {user.email} has been created, and email confirmation sent")
        return user



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id','email', 'username', 'phone_number', 'profile_picture' , 'timezone')



class ProfileFinishSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ( 'username' , 'phone_number','timezone')


class UserEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email']


# =========================================== Update Profile Picture ===========================================

class UpdateProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']

# ===============================================================================================================


































