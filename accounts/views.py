from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser
from .serializers import RegisterSerializer, UserProfileSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
    




# =========================== google login view ===============================
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
import requests
import logging

logger = logging.getLogger(__name__)
CustomUser = get_user_model()

class CustomGoogleLogin(APIView):
    def post(self, request, *args, **kwargs):
        logger.debug(f"Request data: {request.data}")
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'error': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the id_token with Google
        try:
            response = requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}')
            response_data = response.json()
            if 'error_description' in response_data:
                raise Exception(response_data['error_description'])
        except Exception as e:
            logger.error(f"Error verifying id_token: {e}")
            return Response({'error': 'Invalid id_token'}, status=status.HTTP_400_BAD_REQUEST)

        # Create or get the user
        try:
            user = self.get_user_from_response(response_data)
            self.user = user

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return Response({
                'access': access_token,
                'refresh': refresh_token,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during user creation: {e}")
            return Response({'error': 'Error during user creation'}, status=status.HTTP_400_BAD_REQUEST)

    def get_user_from_response(self, response_data):
        email = response_data['email']
        base_username = email.split('@')[0]
        username = base_username

        # Check if the username already exists and generate a unique one if necessary
        if CustomUser.objects.filter(username=username).exists():
            username = self.generate_unique_username(base_username)

        user, created = CustomUser.objects.get_or_create(email=email, defaults={
            'username': username,
            'is_email_verified': True,
            'profile_picture': settings.DEFAULT_PROFILE_PICTURE_URL,  # Set the default profile picture URL

        })

        if created:
            pass

        if not created:
            user.is_email_verified = True
            user.save()

        return user

    def generate_unique_username(self, base_username):
        while True:
            username = f"{base_username}_{get_random_string(5)}"
            if not CustomUser.objects.filter(username=username).exists():
                return username
            




# ========================================   email confirm view ========================================



from allauth.account.views import ConfirmEmailView
from allauth.account.models import EmailConfirmationHMAC
from django.shortcuts import redirect
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CustomConfirmEmailView(ConfirmEmailView):
    def get(self, request, *args, **kwargs):
        logger.info("Entering CustomConfirmEmailView")
        confirmation = EmailConfirmationHMAC.from_key(kwargs['key'])
        if confirmation:
            logger.info("Confirmation found, confirming...")
            confirmation.confirm(request)
            user = confirmation.email_address.user
            user.is_email_verified = True  
            user.save()
            # Redirect to frontend login page with query parameter
            return redirect(f'{settings.FRONTEND_URL}?isAuthenticated=false')  
        else:
            logger.error("Confirmation not found, returning invalid template")
            return redirect(f'{settings.FRONTEND_URL}') 