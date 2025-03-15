import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Task, Board
from accounts.models import CustomUser
from asgiref.sync import sync_to_async


class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.board_group_name = f'board_{self.board_id}'

        # print(f"User details: is_authenticated={self.scope['user'].is_authenticated}, is_superuser={self.scope['user'].is_superuser}, email={self.scope['user'].email}")

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
        elif action == 'add_user':
            await self.add_user(payload)
        elif action == 'delete_user':
            await self.delete_user_from_board(payload)

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
        is_admin = await self.is_admin()
        is_owner = await self.is_owner()
        print(f"is_admin=>>: {is_admin}, is_owner=>>: {is_owner}")

        if not (is_admin or is_owner):
            print("Permission denied: User is neither admin nor owner")
            return

        user_id = payload['user_id']
        new_status = payload['new_status']

        try:
            user = await sync_to_async(CustomUser.objects.get)(id=user_id)
            board = await sync_to_async(Board.objects.get)(id=self.board_id)

            if new_status == 'admin':
                print('Adding user as admin')
                await sync_to_async(board.admins.add)(user)
                await sync_to_async(board.members.remove)(user)
            elif new_status == 'member':
                print('Removing user from admins')
                await sync_to_async(board.admins.remove)(user)
                await sync_to_async(board.members.add)(user)

            await sync_to_async(board.save)()  # Ensure the board is saved after modification

            # Verify if the user is added to the admins
            board = await sync_to_async(Board.objects.get)(id=self.board_id)
            is_user_admin = await sync_to_async(lambda: user in board.admins.all())()
            print(f"User {user.email} is admin: {is_user_admin}")

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
        except Board.DoesNotExist:
            print('Board does not exist:', self.board_id)
            

    async def add_user(self, payload):
        is_admin = await self.is_admin()
        is_owner = await self.is_owner()
        print(f"is_admin: {is_admin}, is_owner: {is_owner}")

        if not (is_admin or is_owner):
            print("Permission denied: User is neither admin nor owner")
            return

        emails = payload['emails']
        board_id = payload['board_id']  # Get the board ID from the payload
        print(f"emails: {emails}, board_id: {board_id}")

        for email in emails:
            try:
                user = await CustomUser.objects.aget(email=email)
                await self.add_user_to_board(user, board_id)  

                print('User added to board:', user.email)
                
                # Notify group about the new user
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
        if not await self.is_admin() or not await self.is_owner():
            return

        user_id = payload['user_id']
        board_id = payload['board_id']

        try:
            user = await CustomUser.objects.aget(id=user_id)
            board = await Board.objects.aget(id=board_id)
            board.members.remove(user)
            await board.asave()

            # Notify group about the user deletion
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
        except (CustomUser.DoesNotExist, Board.DoesNotExist):
            print('User or board does not exist:', user_id, board_id)

    @database_sync_to_async
    def add_user_to_board(self, user, board_id):
        try:
            board = Board.objects.get(id=board_id)
            board.members.add(user)  # Add user to members, not admins
            board.save()
            # print(f'User {user.email} added to board {board_id} as a member')
        except Board.DoesNotExist:
            print(f'Board does not exist: {board_id}')

    @database_sync_to_async
    def is_owner(self):
        try:
            board = Board.objects.get(id=self.board_id)
            # print(f"Board owner: {board.owner}, Current user: {self.scope['user']}")
            return board.owner == self.scope["user"]
        except Board.DoesNotExist:
            print(f"Board does not exist: {self.board_id}")
            return False

    @database_sync_to_async
    def is_admin(self):
        try:
            board = Board.objects.get(id=self.board_id)
            # print(f"Board admins: {board.admins.all()}, Current user: {self.scope['user']}")
            return self.scope["user"] in board.admins.all()
        except Board.DoesNotExist:
            print(f"Board does not exist: {self.board_id}")
            return False
        
    @database_sync_to_async
    def is_member_or_admin(self):
        board = Board.objects.get(id=self.board_id)
        return self.scope["user"] in board.members.all() or self.scope["user"] in board.admins.all() or board.owner == self.scope["user"]

    async def board_message(self, event):
        action = event['action']
        payload = event['payload']

        print(f'Sending message to WebSocket: action: {action}, payload: {payload}')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'action': action,
            'payload': payload
        }))