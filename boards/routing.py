# filepath: /home/guram/Desktop/task_management_app/task_back/taskmainder/boards/routing.py
from django.urls import path
from .consumers import BoardConsumer

websocket_urlpatterns = [
    path('ws/boards/<int:board_id>/', BoardConsumer.as_asgi()),
]