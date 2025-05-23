from rest_framework import serializers
from .models import Board, Task, List, BoardMembership, Notification
from accounts.models import CustomUser
from rest_framework.exceptions import ValidationError

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class ListSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = List
        fields = '__all__'

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'profile_picture']

class BoardUserSerializer(serializers.ModelSerializer):
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'profile_picture', 'user_status']

    def get_user_status(self, obj):
        board = self.context.get('board')
        if board:
            membership = BoardMembership.objects.filter(board=board, user=obj).first()
            if membership:
                return membership.user_status
        return None

class BoardSerializer(serializers.ModelSerializer):
    lists = ListSerializer(many=True, read_only=True)
    board_users = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = '__all__'

    def get_board_users(self, obj):
        memberships = BoardMembership.objects.filter(board=obj)
        users = [membership.user for membership in memberships]
        serializer = BoardUserSerializer(users, many=True, context={'board': obj})
        return serializer.data

    def add_member(self, board, email, user_status):
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise ValidationError("User with this email does not exist.")
        
        if BoardMembership.objects.filter(board=board, user=user).exists():
            raise ValidationError("User is already a member of this board.")
        
        BoardMembership.objects.create(board=board, user=user, user_status=user_status)
        return board
    

# ============================== get user notifications serializer ==============================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'is_read', 'created_at']