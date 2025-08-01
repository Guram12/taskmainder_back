from rest_framework import serializers
from allauth.account.utils import send_email_confirmation
from .models import CustomUser
from sib_api_v3_sdk import TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
from decouple import config
from logging import getLogger
import sib_api_v3_sdk  
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from boards.sendemail import send_email_confirmation







logger = getLogger(__name__)
from allauth.account.models import EmailAddress

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password', 'phone_number', 'profile_picture', 'timezone')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        profile_picture = validated_data.pop('profile_picture', None)

        # Create the user
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            profile_picture=profile_picture,
            timezone=validated_data.get('timezone', 'UTC'),
            phone_number=validated_data.get('phone_number', '')
        )

        # Create an EmailAddress object for the user
        email_address = EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=False,
            primary=True
        )

        # Send email confirmation using Brevo
        try:
            send_email_confirmation(email_address)
            logger.info(f"Email confirmation sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send email confirmation: {e}")
            email_address.delete()
            user.delete()
            raise serializers.ValidationError("Failed to send email confirmation. Please try again later.")

        return user


# ======================================= user profile serializer  =================================================

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id','email', 'username', 'phone_number', 'profile_picture' , 'timezone', 'is_email_verified', 'is_social_account','discord_webhook_url', 'notification_preference')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('timezone', '').lower() == "asia/tbilisi":
            data['timezone'] = "Europe/Tbilisi"
        return data


class ProfileFinishSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'timezone')

    def validate_timezone(self, value):
        if value.lower() == "europe/tbilisi":
            return "Asia/Tbilisi"
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('timezone', '').lower() == "asia/tbilisi":
            data['timezone'] = "Europe/Tbilisi"
        return data

class UserEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email']

class NotificationPreferenceOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['notification_preference']

class DiscordWebhookURLOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['discord_webhook_url']
# =========================================== Update Profile Picture ===========================================

class UpdateProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']

# ===============================================================================================================

class UsernameANDPhoneNumberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'phone_number', 'timezone']


    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('timezone', '').lower() == "asia/tbilisi":
            data['timezone'] = "Europe/Tbilisi"
        return data



















