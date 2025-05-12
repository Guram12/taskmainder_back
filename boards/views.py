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
                        'profile_picture': user.profile_picture.url,
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
                'profile_picture': membership.user.profile_picture.url,
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
    
