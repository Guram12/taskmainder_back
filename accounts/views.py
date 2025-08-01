from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import CustomUser
from .serializers import RegisterSerializer, UserProfileSerializer , UserEmailSerializer \
    , UpdateProfilePictureSerializer, UsernameANDPhoneNumberUpdateSerializer \
    , NotificationPreferenceOnlySerializer , DiscordWebhookURLOnlySerializer

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
    
class UsernameANDPhoneNumberUpdateView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = UsernameANDPhoneNumberUpdateSerializer

    def get_object(self):
        return self.request.user


# ===================================  email list view ====================================

class UserEmailListView(generics.ListAPIView):
    serializer_class = UserEmailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CustomUser.objects.none()  # Start with an empty queryset
        search = self.request.query_params.get('search', None)
        
        if  len(search) <= 2:
            return queryset
        elif search:
            # in this queryset, i should send all emails except email with current user 
            queryset = CustomUser.objects.exclude(email=self.request.user.email).filter(Q(email__icontains=search))
        return queryset
    

# ================================   custom login view ====================================
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate




class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            # Check if the user exists
            user = CustomUser.objects.get(email=email)
            
            # Check if the email is verified
            if not user.is_email_verified:
                return Response({'error': 'Email is not verified'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Authenticate the user
            user = authenticate(request, email=email, password=password)
            if user is not None:
                return super().post(request, *args, **kwargs)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        
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
            'profile_picture': None, 
            'is_social_account': True,

        })

        if created:
            pass

        if not created:
            user.is_email_verified = True
            user.is_social_account = True 

            user.save()

        return user

    def generate_unique_username(self, base_username):
        while True:
            username = f"{base_username}_{get_random_string(5)}"
            if not CustomUser.objects.filter(username=username).exists():
                return username


# ====================================  update timezone view if user logs is with google =========================

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import ProfileFinishSerializer

class ProfileFinishView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileFinishSerializer

    def get_object(self):
        return self.request.user



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
        
        
# ============================================  password reset view =========================================
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode 
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_str




from boards.sendemail import send_password_reset_email  # Import the new function

class PasswordResetView(APIView):
    """
    View to handle sending password reset email using Brevo.
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            if user.is_social_account:
                return Response(
                    {'error': 'This email is associated with Google sign up. Please use Google login.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_str(user.pk).encode('utf-8'))

            # Generate password reset link
            reset_link = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"

            # Use the new Brevo function to send the email
            try:
                send_password_reset_email(email, reset_link, user.username)
                return Response({'message': 'Password reset link has been sent to your email.'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except CustomUser.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        
        
# ========================================  password reset confirm view =========================================

class PasswordResetConfirmView(APIView):
    """
    View to handle password reset confirmation.
    """
    def post(self, request, *args, **kwargs):
        uid = kwargs.get('uidb64')
        token = kwargs.get('token')
        new_password = request.data.get('new_password')

        if not uid or not token or not new_password:
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decode the uid
            logger.info(f"Decoding uid: {uid}")
            uid = force_str(urlsafe_base64_decode(uid))
            logger.info(f"Decoded uid: {uid}")

            # Fetch the user
            user = CustomUser.objects.get(pk=uid)
            logger.info(f"User found: {user.email}")

            # Validate the token
            if not default_token_generator.check_token(user, token):
                logger.warning(f"Invalid or expired token for user: {user.email}")
                return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

            # Set the new password
            user.set_password(new_password)
            user.save()
            logger.info(f"Password reset successfully for user: {user.email}")

            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            logger.error(f"User does not exist for uid: {uid}")
            return Response({'error': 'Invalid user.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# =========================================== Update Profile Picture View ===========================================


class UpdateProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user

        # Check if the request contains a flag to delete the profile picture
        if request.data.get('delete_picture', False):
            if user.profile_picture:
                user.profile_picture.delete(save=False)  # Delete the file from AWS S3
                user.profile_picture = None  # Set the field to None
                user.save()
                return Response({"message": "Profile picture deleted successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No profile picture to delete"}, status=status.HTTP_400_BAD_REQUEST)

        # Otherwise, update the profile picture
        serializer = UpdateProfilePictureSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile picture updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# ===============================================================================================================

from boards.models import BoardMembership, Board  

class AccountDeleteView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated via token

    def delete(self, request, *args, **kwargs):
        user = request.user

        owner_memberships = BoardMembership.objects.filter(user=user, user_status='owner')
        board_ids = owner_memberships.values_list('board_id', flat=True)
        Board.objects.filter(id__in=board_ids).delete()

        user.delete()
        return Response({"message": "Account and owned boards deleted successfully."}, status=status.HTTP_200_OK)


# ============================================   password  change view =========================================
from rest_framework.exceptions import ValidationError

class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        new_password = request.data.get('new_password')

        if not new_password:
            return Response({'error': 'New password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user  # Get the authenticated user from the request
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)

# ==========================================  check if  password is correct ===========================================

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class CheckPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        password = request.data.get('old_password')
        if not password:
            return Response({'detail': 'Password is required.'}, status=400)
        user = request.user
        is_correct = user.check_password(password)
        return Response({'is_correct': is_correct})




class NotificationPreferenceUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        serializer = NotificationPreferenceOnlySerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class DiscordWebhookURLUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = DiscordWebhookURLOnlySerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        webhook_url = serializer.validated_data.get('discord_webhook_url', None)

        # If webhook URL is being deleted (set to empty or None), set notification_preference to 'email'
        if webhook_url in [None, '', 'null']:
            user.discord_webhook_url = None
            user.notification_preference = 'email'
            user.save()
            return Response({'discord_webhook_url': None, 'notification_preference': 'email'})
        else:
            serializer.save()
            return Response(serializer.data)