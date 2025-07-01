from rest_framework import serializers
from allauth.account.utils import send_email_confirmation
from .models import CustomUser
from django.conf import settings
from sib_api_v3_sdk import TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException
from decouple import config
from logging import getLogger
import sib_api_v3_sdk  
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from allauth.account.models import EmailConfirmationHMAC


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
            self.send_email_confirmation(email_address)
            logger.info(f"Email confirmation sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send email confirmation: {e}")
            raise serializers.ValidationError("Failed to send email confirmation. Please try again later.")

        return user

    def send_email_confirmation(self, email_address):
        """
        Sends an email confirmation using Brevo.
        """
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = config('BREVO_API_KEY')

        api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        # Generate the confirmation key
        confirmation = EmailConfirmationHMAC(email_address)
        confirmation_key = confirmation.key

        # Define the email content
        send_smtp_email = SendSmtpEmail(
            sender={"email": "guramshanidze44@gmail.com", "name": "Task Reminder"},  # Verified sender email
            to=[{"email": email_address.email}],
            template_id=4,  # Replace with your Brevo email confirmation template ID
            params={
                "username": email_address.user.username,
                "confirmation_link": f"{settings.BACKEND_URL}/acc/confirm-email/{confirmation_key}/",  # Use the generated key
            },
            headers={"X-Mailin-Tag": "email_confirmation"}
        )

        try:
            response = api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email confirmation sent to {email_address.email}. Brevo response: {response}")
        except ApiException as e:
            logger.error(f"Error sending email confirmation: {e}")
            raise Exception("Failed to send email confirmation.")


# ======================================= user profile serializer  =================================================

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id','email', 'username', 'phone_number', 'profile_picture' , 'timezone', 'is_email_verified', 'is_social_account')



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

class UsernameANDPhoneNumberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'phone_number']

























