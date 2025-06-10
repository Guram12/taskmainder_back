from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, ListViewSet, TaskViewSet , delete_user_from_board, get_board_users \
    , SendInvitationEmailView, AcceptInvitationView , save_subscription, get_notifications \
    , mark_all_notifications_as_read, delete_notification , delete_all_notifications, self_delete_from_board \
    , UpdateBoardBackgroundImageView , DeleteBoardBackgroundImageView , get_user_boards_with_status \
    , CreateBoardFromTemplateView

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

    path('notifications/', get_notifications, name='get_notifications'),
    path('notifications/mark-all-as-read/', mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('notifications/<int:notification_id>/delete/', delete_notification, name='delete_notification'),
    path('notifications/delete-all/', delete_all_notifications, name='delete_all_notifications'),


    path('boards/<int:board_id>/users/<int:user_id>/delete/', delete_user_from_board, name='delete_user_from_board'),
    path('boards/<int:board_id>/self-delete/', self_delete_from_board, name='self_delete_from_board'),

    path('boards/<int:pk>/update-background-image/', UpdateBoardBackgroundImageView.as_view(), name='update-board-background-image'),
    path('boards/<int:pk>/delete-background-image/', DeleteBoardBackgroundImageView.as_view(), name='delete-board-background-image'),

    path('user-boards-status/', get_user_boards_with_status, name='user_boards_status'),

    path('create-from-template/', CreateBoardFromTemplateView.as_view(), name='create_board_from_template'),

]




# sudo apt-get update
# sudo apt-get install redis-server
# sudo service redis-server start
# sudo service redis-server status
# sudo systemctl enable redis-server


# export DJANGO_SETTINGS_MODULE=taskmainder.settings
# daphne -b 0.0.0.0 -p 8000 taskmainder.asgi:application