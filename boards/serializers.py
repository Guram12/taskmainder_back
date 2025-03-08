from rest_framework import serializers
from .models import Board, Task, List
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
    status = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'profile_picture', 'status']

    def get_status(self, obj):
        board = self.context['board']
        if obj == board.owner:
            return 'owner'
        return 'member'

class BoardSerializer(serializers.ModelSerializer):
    lists = ListSerializer(many=True, read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    board_users = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = '__all__'

    def get_board_users(self, obj):
        users = [obj.owner] + list(obj.members.all())
        serializer = BoardUserSerializer(users, many=True, context={'board': obj})
        return serializer.data

    def add_member(self, board, email):
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise ValidationError("User with this email does not exist.")
        
        if user in board.members.all():
            raise ValidationError("User is already a member of this board.")
        
        board.members.add(user)
        return board