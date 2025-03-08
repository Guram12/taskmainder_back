import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Task, List
from accounts.models import CustomUser

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

        print(f'Received action: {action}, payload: {payload}')

        if action == 'move_task':
            await self.move_task(payload)
        elif action == 'set_status':
            await self.set_status(payload)

    async def move_task(self, payload):
        print('Moving task:', payload)
        task_id = payload['task_id']
        source_list_id = payload['source_list_id']
        target_list_id = payload['target_list_id']

        try:
            task = await Task.objects.aget(id=task_id)
            task.list_id = target_list_id
            await task.asave()

            # Notify group about the task movement
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'move_task',
                    'payload': {
                        'task_id': task_id,
                        'source_list_id': source_list_id,
                        'target_list_id': target_list_id
                    }
                }
            )
        except Task.DoesNotExist:
            print('Task does not exist:', task_id)

    async def set_status(self, payload):
        user_id = payload['user_id']
        new_status = payload['new_status']

        try:
            user = await CustomUser.objects.aget(id=user_id)
            user.status = new_status
            await user.asave()

            # Notify group about the user status change
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'set_status',
                    'payload': {
                        'user_id': user_id,
                        'new_status': new_status
                    }
                }
            )
        except CustomUser.DoesNotExist:
            print('User does not exist:', user_id)

    async def board_message(self, event):
        action = event['action']
        payload = event['payload']

        print(f'Sending message to WebSocket: action: {action}, payload: {payload}')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'action': action,
            'payload': payload
        }))