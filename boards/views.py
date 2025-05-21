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




@api_view(['DELETE'])
def delete_user_from_board(request, board_id, user_id):
    print(f'deleting user {user_id} from board {board_id} ' )
    try:
        membership = BoardMembership.objects.get(board_id=board_id, user_id=user_id)
        membership.delete()
        return Response({'status': 'success'})
    except BoardMembership.DoesNotExist:
        return Response({'error': 'User not found in board'}, status=404)
    


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

            for subscription in subscriptions:
                try:
                    webpush(
                        subscription_info=subscription.subscription_info,
                        data=json.dumps({
                            'title': 'Board Invitation Accepted',
                            'body': f'{user.username} has joined your board "{board.name}".',
                        }),
                        vapid_private_key='4aMg0XhG2sXL0LAftafusC0jpOorGDb8efcyxsCNjvw', 
                        vapid_claims={
                            'sub': 'mailto:your-email@example.com' 
                        }
                    )
                except WebPushException as e:
                    print(f"Web push failed: {e}")

            # Redirect to the frontend
            return redirect(f'{settings.FRONTEND_URL}?isAuthenticated=true')

        except Exception as e:
            return Response({'error': 'Invalid or expired token'}, status=400)
        

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