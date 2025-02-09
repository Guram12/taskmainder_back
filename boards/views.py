from .serializers import TaskSerializer, BoardSerializer, ListSerializer
from .models import Board, List, Task
from rest_framework import viewsets
from .permisions import IsOwner
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)



class ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        board_id = self.request.query_params.get('board_id')
        return self.queryset.filter(board_id=board_id)



class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        list_id = self.request.query_params.get('list_id')
        if list_id:
            return self.queryset.filter(list_id=list_id)
        return self.queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def move(self, request, pk=None):
        task = self.get_object()
        new_list_id = request.data.get('new_list_id')
        try:
            new_list = List.objects.get(id=new_list_id)
        except List.DoesNotExist:
            return Response({'error': 'List not found'}, status=status.HTTP_404_NOT_FOUND)
        
        task.list = new_list
        task.save()
        return Response({'status': 'task moved'}, status=status.HTTP_200_OK)































