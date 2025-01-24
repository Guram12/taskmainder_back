from rest_framework import serializers
from .models import Board , Task, List





class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class ListSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = List
        fields = '__all__'

class BoardSerializer(serializers.ModelSerializer):
    lists = ListSerializer(many=True, read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Board
        fields = '__all__'
        extra_fields = ['owner_email']


    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['owner'] = representation.pop('owner_email')
        return representation

















