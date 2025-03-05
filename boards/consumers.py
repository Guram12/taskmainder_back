# filepath: /home/guram/Desktop/task_management_app/task_back/taskmainder/boards/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.board_group_name = f'board_{self.board_id}'

        # Join board group
        await self.channel_layer.group_add(
            self.board_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave board group
        await self.channel_layer.group_discard(
            self.board_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data['action']
        payload = data['payload']

        # Send message to board group
        await self.channel_layer.group_send(
            self.board_group_name,
            {
                'type': 'board_message',
                'action': action,
                'payload': payload
            }
        )

    async def board_message(self, event):
        action = event['action']
        payload = event['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'action': action,
            'payload': payload
        }))