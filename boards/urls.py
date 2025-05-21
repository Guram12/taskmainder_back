from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, ListViewSet, TaskViewSet , delete_user_from_board, get_board_users \
, SendInvitationEmailView, AcceptInvitationView , save_subscription

router = DefaultRouter()
router.register(r'boards', BoardViewSet)
router.register(r'lists', ListViewSet)
router.register(r'tasks', TaskViewSet)



urlpatterns = [
    path('', include(router.urls)),

    path('boards/<int:board_id>/users/', get_board_users, name='get_board_users'),
    path('boards/<int:board_id>/users/<int:user_id>/delete/', delete_user_from_board, name='delete_user_from_board'),

    #  send invitation email and add user to board
    path('boards/<int:board_id>/send-invitation/', SendInvitationEmailView.as_view(), name='send_invitation_email'),
    path('accept-invitation/', AcceptInvitationView.as_view(), name='accept_invitation'),

    # save subscription
    path('save-subscription/', save_subscription, name='save_subscription'),
]





# sudo apt-get update
# sudo apt-get install redis-server
# sudo service redis-server start
# sudo service redis-server status
# sudo systemctl enable redis-server


# export DJANGO_SETTINGS_MODULE=taskmainder.settings
# daphne -b 0.0.0.0 -p 8000 taskmainder.asgi:application