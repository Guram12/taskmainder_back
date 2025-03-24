import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Task, Board, BoardMembership
from accounts.models import CustomUser
from asgiref.sync import sync_to_async

class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.board_group_name = f'board_{self.board_id}'

        await self.channel_layer.group_add(
            self.board_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.board_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data['action']
        payload = data['payload']

        if action == 'move_task':
            await self.move_task(payload)
        elif action == 'set_status':
            await self.set_status(payload)
        elif action == 'add_user':
            await self.add_user(payload)
        elif action == 'delete_user':
            await self.delete_user_from_board(payload)

    async def move_task(self, payload):
        task_id = payload['task_id']
        source_list_id = payload['source_list_id']
        target_list_id = payload['target_list_id']

        try:
            task = await Task.objects.aget(id=task_id)
            task.list_id = target_list_id
            await task.asave()

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
            user = await sync_to_async(CustomUser.objects.get)(id=user_id)
            membership = await sync_to_async(BoardMembership.objects.get)(board_id=self.board_id, user=user)
            membership.user_status = new_status
            await sync_to_async(membership.save)()

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
        except BoardMembership.DoesNotExist:
            print('Membership does not exist:', user_id, self.board_id)

    async def add_user(self, payload):
        emails = payload['emails']
        board_id = payload['board_id']

        for email in emails:
            try:
                user = await CustomUser.objects.aget(email=email)
                await self.add_user_to_board(user, board_id)

                await self.channel_layer.group_send(
                    self.board_group_name,
                    {
                        'type': 'board_message',
                        'action': 'add_user',
                        'payload': {
                            'user_id': user.id,
                            'email': user.email,
                            'username': user.username,
                            'profile_picture': user.profile_picture.url,
                        }
                    }
                )
            except CustomUser.DoesNotExist:
                print('User does not exist:', email)

    async def delete_user_from_board(self, payload):
        user_id = payload['user_id']
        board_id = payload['board_id']
        print(self.scope['user'])
        if not await self.is_owner_or_admin():
            print('Permission denied: Only owners and admins can delete users.')
            return

        try:
            user = await CustomUser.objects.aget(id=user_id)
            membership = await BoardMembership.objects.aget(board_id=board_id, user=user)
            await membership.adelete()

            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'delete_user',
                    'payload': {
                        'user_id': user_id,
                    }
                }
            )
            
        except (CustomUser.DoesNotExist, BoardMembership.DoesNotExist):
            print('User or membership does not exist:', user_id, board_id)

    @database_sync_to_async
    def is_owner_or_admin(self):
        try:
            membership = BoardMembership.objects.get(board_id=self.board_id, user=self.scope["user"])
            return membership.user_status in ['owner', 'admin']
        except BoardMembership.DoesNotExist:
            return False

    @database_sync_to_async
    def add_user_to_board(self, user, board_id):
        try:
            board = Board.objects.get(id=board_id)
            BoardMembership.objects.create(board=board, user=user, user_status='member')
        except Board.DoesNotExist:
            print(f'Board does not exist: {board_id}')

    @database_sync_to_async
    def is_owner(self):
        try:
            membership = BoardMembership.objects.get(board_id=self.board_id, user=self.scope["user"])
            return membership.user_status == 'owner'
        except BoardMembership.DoesNotExist:
            return False

    @database_sync_to_async
    def is_admin(self):
        try:
            membership = BoardMembership.objects.get(board_id=self.board_id, user=self.scope["user"])
            return membership.user_status == 'admin'
        except BoardMembership.DoesNotExist:
            return False

    async def board_message(self, event):
        action = event['action']
        payload = event['payload']

        await self.send(text_data=json.dumps({
            'action': action,
            'payload': payload
        }))