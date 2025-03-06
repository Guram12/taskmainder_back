from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializers import TaskSerializer, BoardSerializer, ListSerializer
from .models import Board, List, Task
from rest_framework import viewsets
from .permissions import IsOwner
from rest_framework.permissions import IsAuthenticated

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
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

class ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return self.queryset.filter(board__owner=self.request.user)

    def perform_create(self, serializer):
        list_instance = serializer.save()
        self.notify_list_update(list_instance.board.id, 'create', serializer.data)

    def perform_update(self, serializer):
        list_instance = serializer.save()
        self.notify_list_update(list_instance.board.id, 'update', serializer.data)

    def perform_destroy(self, instance):
        board_id = instance.board.id
        instance.delete()
        self.notify_list_update(board_id, 'delete', {'id': instance.id})

    def notify_list_update(self, board_id, action, payload):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'board_{board_id}',
            {
                'type': 'list_message',
                'action': action,
                'payload': payload
            }
        )

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return self.queryset.filter(list__board__owner=self.request.user)

    def perform_create(self, serializer):
        task_instance = serializer.save()
        self.notify_task_update(task_instance.list.board.id, 'create', serializer.data)

    def perform_update(self, serializer):
        task_instance = serializer.save()
        self.notify_task_update(task_instance.list.board.id, 'update', serializer.data)

    def perform_destroy(self, instance):
        board_id = instance.list.board.id
        instance.delete()
        self.notify_task_update(board_id, 'delete', {'id': instance.id})

    def notify_task_update(self, board_id, action, payload):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'board_{board_id}',
            {
                'type': 'task_message',
                'action': action,
                'payload': payload
            }
        )