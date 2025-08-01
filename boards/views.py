from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializers import TaskSerializer, BoardSerializer, ListSerializer
from .models import Board, List, Task, BoardMembership
from rest_framework import viewsets , status
from .permissions import IsOwnerOrMember
from rest_framework.permissions import IsAuthenticated
from django.db import models
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import CustomUser
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
# import redirect 


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(
            models.Q(boardmembership__user=user)
        )

    def perform_create(self, serializer):
        board = serializer.save()
        BoardMembership.objects.create(board=board, user=self.request.user, user_status='owner')
        self.notify_board_update(board.id, 'create', serializer.data)

    def perform_update(self, serializer):
        board = serializer.save()
        self.notify_board_update(board.id, 'update', serializer.data)

    def perform_destroy(self, instance):
        board_id = instance.id
        instance.delete()
        self.notify_board_update(board_id, 'delete', {'id': board_id})

    def notify_board_update(self, board_id, action, payload):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'board_{board_id}',
            {
                'type': 'board_message',
                'action': action,
                'payload': payload
            }
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_users(self, request, pk=None):
        board = self.get_object()
        emails = request.data.get('emails', [])
        users = []

        for email in emails:
            try:
                user = CustomUser.objects.get(email=email)
                membership, created = BoardMembership.objects.get_or_create(board=board, user=user, defaults={'user_status': 'member'})
                if created:
                    users.append({
                        'id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'profile_picture': user.profile_picture.url if user.profile_picture else None,
                        'user_status': membership.user_status,
                    })
            except CustomUser.DoesNotExist:
                continue
        return Response(users, status=status.HTTP_200_OK)


# ================================== list viewset ==================================

class ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ListSerializer

    def get_queryset(self):
        user = self.request.user
        return List.objects.filter(
            models.Q(board__boardmembership__user=user)
        )

# ================================== task viewset ==================================

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            models.Q(list__board__boardmembership__user=user)
        )



# =============================== add user to board =================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_board_users(request, board_id):
    try:
        memberships = BoardMembership.objects.filter(board_id=board_id)
        users = [
            {
                'id': membership.user.id,
                'email': membership.user.email,
                'username': membership.user.username,
                'profile_picture': membership.user.profile_picture.url if membership.user.profile_picture else None,
                'user_status': membership.user_status,
            }
            for membership in memberships
        ]
        return Response(users)
    except BoardMembership.DoesNotExist:
        return Response({'error': 'Board not found -->> !!! '}, status=404)





# ==========================================  send user board invite email  ==========================================
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import urlencode
from .sendemail import send_board_invitation_email
import secrets
from rest_framework.views import APIView
from .models import BoardInvitation



class SendInvitationEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, board_id):
        emails = request.data.get('email', [])  # Expecting an array of emails
        if not isinstance(emails, list):
            return Response({'error': 'Invalid data format. "email" should be a list of emails.'}, status=400)

        board = get_object_or_404(Board, id=board_id)
        failed_emails = []

        for email in emails:
            try:
                # Generate a unique token for each email
                token = secrets.token_urlsafe(32)

                # Save the invitation in the database
                BoardInvitation.objects.create(email=email, board=board, token=token)

                # Generate the invitation link
                base_url = request.build_absolute_uri(reverse('accept_invitation'))
                query_params = urlencode({'token': token})
                invitation_link = f"{base_url}?{query_params}"

                # Send the email using the existing email-sending function
                send_board_invitation_email(
                    email=email,
                    username=request.user.username,
                    board_name=board.name,
                    invitation_link=invitation_link,
                )
            except Exception as e:
                failed_emails.append({'email': email, 'error': str(e)})

        if failed_emails:
            return Response({
                'message': 'Some invitations failed to send.',
                'failed_emails': failed_emails
            }, status=207)  # 207 Multi-Status for partial success

        return Response({'message': 'All invitations sent successfully!'}, status=200)
    

# ====================================================== eccept invitation ==========================================
from django.shortcuts import redirect
from django.conf import settings
from pywebpush import webpush, WebPushException




from .models import Notification

class AcceptInvitationView(APIView):
    def get(self, request):
        token = request.GET.get('token')

        try:
            # Retrieve the invitation and associated board/user
            invitation = get_object_or_404(BoardInvitation, token=token)
            board = invitation.board
            user = get_object_or_404(CustomUser, email=invitation.email)

            # Create the BoardMembership
            BoardMembership.objects.create(
                user=user,
                board=board,
                user_status='member',
                is_invitation_accepted=True
            )

            # Delete the invitation after it's accepted
            invitation.delete()

            # Send push notification to the inviter
            inviter = board.boardmembership_set.filter(user_status='owner').first().user
            subscriptions = PushSubscription.objects.filter(user=inviter)

            notification_title = 'Board Invitation Accepted'
            notification_body = f'{user.username} has joined your board "{board.name}".'

            # Save the notification in the database
            notification = Notification.objects.create(
                user=inviter,
                title=notification_title,
                body=notification_body
            )

            for subscription in subscriptions:
                try:
                    webpush(
                        subscription_info=subscription.subscription_info,
                        data=json.dumps({
                            'type': 'BOARD_INVITATION_ACCEPTED', 
                            'title': notification_title,
                            'body': notification_body,
                            'boardName': board.name,
                            'invitedUserEmail': user.email,
                            'invitedUserName': user.username,
                            'notification_id': notification.id, 
                            'is_read': notification.is_read,
                            'board_id': board.id, 

                        }),
                        vapid_private_key='4aMg0XhG2sXL0LAftafusC0jpOorGDb8efcyxsCNjvw', 
                        vapid_claims={
                            'sub': 'mailto:mydailydoer@gmail.com' 
                        }
                    )
                except WebPushException as e:
                    print(f"Web push failed: {e}")

            # Redirect to the frontend
            return redirect(f'{settings.FRONTEND_URL}?isAuthenticated=true')

        except Exception as e:
            return redirect(f'{settings.FRONTEND_URL}?isAuthenticated=false&invitation=error')

# ================================================  get user notifications ==========================================

from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)



# ====================================  delete user from board and send notification =====================================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_from_board(request, board_id, user_id):
    print(f'Deleting user {user_id} from board {board_id}')
    try:
        membership = BoardMembership.objects.get(board_id=board_id, user_id=user_id)
        user = membership.user
        board = membership.board

        # Delete the membership
        membership.delete()

        # Send a notification to the removed user
        notification_title = "Removed from Board"
        notification_body = f"You have been removed from the board '{board.name}'."

        notification = Notification.objects.create(
            user=user,
            title=notification_title,
            body=notification_body
        )

        # Optionally, send a push notification if the user has a subscription
        subscriptions = PushSubscription.objects.filter(user=user)
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info=subscription.subscription_info,
                    data=json.dumps({
                        'type': 'USER_REMOVED_FROM_BOARD',  # New type for this notification
                        'title': notification_title,
                        'body': notification_body,
                        'boardName': board.name,
                        'removedUserEmail': user.email,
                        'notification_id': notification.id, 
                        'is_read': notification.is_read,

                    }),
                    vapid_private_key='4aMg0XhG2sXL0LAftafusC0jpOorGDb8efcyxsCNjvw',
                    vapid_claims={
                        'sub': 'mailto:mydailydoer@gmail.com'
                    }
                )
            except WebPushException as e:
                print(f"Web push failed: {e}")

        return Response({'status': 'success', 'message': 'User removed from board and notified.'})
    except BoardMembership.DoesNotExist:
        return Response({'error': 'User not found in board'}, status=404)










# ============================================= push notification ==========================================from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import PushSubscription
import json


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
def save_subscription(request):
    if request.method == 'POST':
        print('saving subscription')
        data = json.loads(request.body)
        user = request.user  # Authenticated user

        PushSubscription.objects.update_or_create(
            user=user,
            defaults={'subscription_info': data}
        )
        return JsonResponse({'message': 'Subscription saved successfully!'})



# ============================================= mark all notifications as read ==========================================


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_as_read(request):
    user = request.user
    unread_notifications = Notification.objects.filter(user=user, is_read=False)
    unread_notifications.update(is_read=True)  # Mark all as read in bulk
    return Response({'message': 'All unread notifications marked as read.'})

# ================================================  delete specific Notification ==========================================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    try:
        # Ensure the notification belongs to the authenticated user
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return Response({'message': 'Notification deleted successfully.'}, status=200)
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found.'}, status=404)


# ================================================  delete all Notification ==========================================
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_notifications(request):
    user = request.user
    Notification.objects.filter(user=user).delete()
    return Response({'message': 'All notifications deleted successfully.'}, status=200)

# ================================================ self delete from board =========================================================


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def self_delete_from_board(request, board_id):
    user = request.user
    try:
        membership = BoardMembership.objects.get(board_id=board_id, user=user)
        board = membership.board

        # Prevent the owner from deleting themselves
        if membership.user_status == 'owner':
            return Response({'error': 'Owner cannot delete themselves from the board.'}, status=403)

        # Delete the membership
        membership.delete()

        # Send a notification to the user who left the board
        notification_title = "Left Board"
        notification_body = f"You have left the board '{board.name}'."
        Notification.objects.create(
            user=user,
            title=notification_title,
            body=notification_body
        )

        # Notify other board members about the user's departure
        other_memberships = BoardMembership.objects.filter(board=board).exclude(user=user)
        for other_membership in other_memberships:
            other_user = other_membership.user
            notification_title = "Board Member Left"
            notification_body = f"{user.username} has left the board '{board.name}'."
            Notification.objects.create(
                user=other_user,
                title=notification_title,
                body=notification_body
            )

            #  send a push notification if the user has a subscription
            subscriptions = PushSubscription.objects.filter(user=other_user)
            for subscription in subscriptions:
                try:
                    webpush(
                        subscription_info=subscription.subscription_info,
                        data=json.dumps({
                            'type': 'USER_LEFT_BOARD',
                            'title': notification_title,
                            'body': notification_body,
                            'boardName': board.name,
                            'leftUserEmail': user.email,
                            'leftUserName': user.username,
                        }),
                        vapid_private_key='4aMg0XhG2sXL0LAftafusC0jpOorGDb8efcyxsCNjvw',
                        vapid_claims={
                            'sub': 'mailto:mydailydoer@gmail.com'
                        }
                    )
                except WebPushException as e:
                    print(f"Web push failed: {e}")

        return Response({'status': 'success', 'message': 'You have left the board and notifications have been sent.'})
    except BoardMembership.DoesNotExist:
        return Response({'error': 'You are not a member of this board.'}, status=404)



# ============================== Update Board Background Image View ==============================


class UpdateBoardBackgroundImageView(APIView):
    def patch(self, request, pk):
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response({"error": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

        if 'background_image' not in request.data:
            return Response({"error": "No background_image provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Delete the old background image from AWS S3 if it exists
        if board.background_image:
            board.background_image.delete(save=False)

        # Update the background image with the new one
        board.background_image = request.data['background_image']
        board.save()

        return Response({"message": "Background image updated successfully.", "background_image": board.background_image.url}, status=status.HTTP_200_OK)
    # ============================== Delete Board Background Image View ==============================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Board

class DeleteBoardBackgroundImageView(APIView):
    def delete(self, request, pk):
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response({"error": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

        if not board.background_image:
            return Response({"error": "No background image to delete."}, status=status.HTTP_400_BAD_REQUEST)

        # Delete the file from AWS S3 or the configured storage backend
        board.background_image.delete(save=False)

        # Remove the reference from the database
        board.background_image = None
        board.save()

        return Response({"message": "Background image deleted successfully."}, status=status.HTTP_200_OK)


# ================================================ get user boards with status ==========================================


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_boards_with_status(request):
    user = request.user
    memberships = BoardMembership.objects.filter(user=user).select_related('board')
    data = [
        {
            'board_id': membership.board.id,
            'board_name': membership.board.name,
            'user_status': membership.user_status,
        }
        for membership in memberships
    ]
    return Response(data)



# ===================================== template  create viewset    =====================================
from rest_framework.parsers import MultiPartParser, FormParser


class CreateBoardFromTemplateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        name = request.data.get("name")
        background_image = request.FILES.get("background_image")
        lists = request.data.get("lists")
        import json
        lists = json.loads(lists) if lists else []

        board = Board.objects.create(name=name, background_image=background_image)
        BoardMembership.objects.create(
            board=board,
            user=request.user,
            user_status='owner',
            is_invitation_accepted=True
        )
        print(f'Creating board with name: {name} and background image: {background_image}')
        for list_data in lists:
            list_obj = List.objects.create(name=list_data["name"], board=board)
            for task_data in list_data.get("tasks", []):
                Task.objects.create(
                    title=task_data["title"],
                    description=task_data.get("description", ""),
                    due_date=task_data.get("due_date"),
                    list=list_obj,
                    priority=task_data.get("priority"),
                    order=task_data.get("order", 0)
                )

        serializer = BoardSerializer(board)
        return Response(serializer.data, status=status.HTTP_201_CREATED)