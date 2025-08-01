from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView 
from .views import RegisterView, UserProfileView, CustomGoogleLogin , CustomConfirmEmailView \
    , CustomTokenObtainPairView ,ProfileFinishView , UserEmailListView , UpdateProfilePictureView \
    , PasswordResetView, PasswordResetConfirmView , UsernameANDPhoneNumberUpdateView ,AccountDeleteView \
    , PasswordChangeView , CheckPasswordView , NotificationPreferenceUpdateView, DiscordWebhookURLUpdateView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    path('social/login/token/', CustomGoogleLogin.as_view(), name='google_login'),
    path('social/', include('allauth.urls')),

    # email confirm end point 
    path('confirm-email/<str:key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),
    path('profile-finish/', ProfileFinishView.as_view(), name='update_timezone'), 
    path('user-emails/', UserEmailListView.as_view(), name='user_emails'), 
    path('update-profile-picture/', UpdateProfilePictureView.as_view(), name='update-profile-picture'),

    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('update-username-phone/', UsernameANDPhoneNumberUpdateView.as_view(), name='update_username_phone'),
    path('check-old-password/', CheckPasswordView.as_view(), name='check-password'),

    path('delete-account/', AccountDeleteView.as_view(), name='delete_account'),
    path('password-change/', PasswordChangeView.as_view(), name='password_change'),

    path('notification-preference/', NotificationPreferenceUpdateView.as_view(), name='notification_preference_update'),
    path('discord-webhook-url/', DiscordWebhookURLUpdateView.as_view(), name='discord_webhook_url_update'),
]





























