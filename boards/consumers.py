import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Task, Board, BoardMembership, List
from accounts.models import CustomUser
from asgiref.sync import sync_to_async
from .serializers import BoardSerializer
from datetime import datetime
from django.db import models
from .utils import convert_to_utc






class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.board_group_name = f'board_{self.board_id}'

        await self.channel_layer.group_add(
            self.board_group_name,
            self.channel_name
        )

        await self.accept()

        # when user connects, send the full board state
        # This is a placeholder for the actual logic to fetch the board state
        board = await sync_to_async(Board.objects.get)(id=self.board_id)
        board_data = await sync_to_async(lambda: BoardSerializer(board).data)()

        # print('Sending full board state:::', board_data)
        await self.send(text_data=json.dumps({
            'action': 'full_board_state',
            'payload': board_data,
        }))

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
        elif action == 'add_list':
            await self.add_list(payload)
        elif action == 'delete_list':
            await self.delete_list(payload)
        elif action == 'edit_list_name':
            await self.edit_list_name(payload)
        elif action == 'add_task':
            await self.add_task(payload)
        elif action == "delete_task":
            await self.task_delete(payload)
        elif action == 'update_task':
            await self.update_task(payload)
        elif action == 'reorder_task':
            await self.reorder_task(payload)
            
        elif action == 'update_board_name': 
            await self.update_board_name(payload)
        elif action == 'delete_board':
            await self.delete_board(payload)
# =============================================  Task Methods =============================================

    async def add_task(self, payload):
        task_title = payload['title']
        list_id = payload['list']
        print('Adding task:', task_title, list_id)
        try:
            # Fetch the list to which the task will be added
            task_list = await sync_to_async(List.objects.get)(id=list_id)
            # Create the new task
            new_task = await sync_to_async(task_list.tasks.create)(
                title=task_title,
                description=payload.get('description', ''),
                due_date=payload.get('due_date', None)
            )

            # Notify all clients in the board group about the new task
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'add_task',
                    'payload': {
                        'id': new_task.id,
                        'title': new_task.title,
                        'description': new_task.description,
                        'list': list_id,
                        'created_at': new_task.created_at.isoformat(),
                        'due_date': new_task.due_date.isoformat() if new_task.due_date else None,
                        'completed': new_task.completed,
                    }
                }
            )
        except List.DoesNotExist:
            print('List does not exist:', list_id)


    async def update_task(self, payload):
        task_id = payload['task_id']
        updated_title = payload.get('title', None)
        updated_due_date = payload.get('due_date', None)  # Can be null or empty
        updated_description = payload.get('description', None)
        completed = payload.get('completed', None)
        user_timezone = payload.get('user_timezone', 'UTC')  # Get user's timezone from payload
        print('Updating task:', task_id, updated_title, updated_due_date, updated_description, completed)

        try:
            task = await Task.objects.aget(id=task_id)

            if updated_title is not None:
                task.title = updated_title
            if updated_description is not None:
                task.description = updated_description
            if updated_due_date is not None:
                if updated_due_date.strip():  # If not empty
                    try:
                        updated_due_date_utc = convert_to_utc(updated_due_date, user_timezone)
                        task.due_date = updated_due_date_utc
                    except Exception as e:
                        print(f"Error converting due_date: {e}")
                        updated_due_date_utc = None
                else:
                    # If empty string, set due_date to None
                    task.due_date = None
            else:
                # If due_date is explicitly null, set it to None
                task.due_date = None

            if completed is not None:
                task.completed = completed

            # Save the updated task
            await task.asave()

            # Notify all clients in the board group about the updated task
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'update_task',
                    'payload': {
                        'id': task.id,
                        'title': task.title,
                        'description': task.description,
                        'list': task.list_id,
                        'created_at': task.created_at.isoformat(),
                        'due_date': task.due_date.isoformat() if task.due_date else None,
                        'completed': task.completed,
                    }
                }
            )
        except Task.DoesNotExist:
            print('Task does not exist:', task_id)
            

    async def task_delete(self, payload):
        task_id = payload['task_id']
        print('Deleting task:', task_id)

        try:
            task = await Task.objects.aget(id=task_id)
            list_id = task.list_id 
            await task.adelete()

            # Notify all clients in the board group about the deleted task
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'delete_task',
                    'payload': {
                        'task_id': task_id,
                        'list_id': list_id,
                    }
                }
            )
        except Task.DoesNotExist:
            print('Task does not exist:', task_id)


    async def move_task(self, payload):
        task_id = payload['task_id']
        source_list_id = payload['source_list_id']
        target_list_id = payload['target_list_id']

        try:
            task = await Task.objects.aget(id=task_id)

            # Fetch the highest order number in the target list
            max_order = await sync_to_async(lambda: Task.objects.filter(list_id=target_list_id).aggregate(max_order=models.Max('order'))['max_order'])()
            new_order = (max_order or 0) + 1  # If no tasks exist, start with order 1

            # Update the task's list and order
            task.list_id = target_list_id
            task.order = new_order
            await task.asave()

            # Notify all clients in the board group about the moved task
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'move_task',
                    'payload': {
                        'task_id': task_id,
                        'source_list_id': source_list_id,
                        'target_list_id': target_list_id,
                        'new_order': new_order
                    }
                }
            )
        except Task.DoesNotExist:
            print('Task does not exist:', task_id)

    async def reorder_task(self, payload):
        list_id = payload['list_id']
        task_order = payload['task_order']
        print(f"Reordering tasks in list {list_id}: {task_order}")

        try:
            task_list = await sync_to_async(List.objects.get)(id=list_id)
            tasks = await sync_to_async(list)(task_list.tasks.all())

            # Update the order of tasks
            for index, task_id in enumerate(task_order):
                task = next((t for t in tasks if t.id == task_id), None)
                if task:
                    task.order = index
                    await sync_to_async(task.save)()

            # Notify all clients about the updated order
            print(f"Reordering tasks in list {list_id}: {task_order}")
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'reorder_task',
                    'payload': {'list_id': list_id, 'task_order': task_order},
                }
            )
        except List.DoesNotExist:
            print(f"List {list_id} does not exist.")


# =============================================  List Methods =============================================


    async def add_list(self, payload):
        list_name = payload['name']
        board_id = payload['board']

        try:
            board = await Board.objects.aget(id=board_id)
            new_list = await sync_to_async(board.lists.create)(name=list_name)

            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'add_list',
                    'payload': {
                        'id': new_list.id,
                        'name': new_list.name,
                        'created_at': new_list.created_at.isoformat(),
                        'board': board_id,
                        'tasks': []
                    }
                }
            )
        except Board.DoesNotExist:
            print('Board does not exist:', board_id)


    async def edit_list_name(self, payload):
        list_id = payload['list_id']
        new_name = payload['new_name']
        print('Editing list name:', list_id, new_name)

        try:
            task_list = await List.objects.aget(id=list_id)

            task_list.name = new_name
            await task_list.asave()

            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'edit_list_name',
                    'payload': {
                        'list_id': list_id,
                        'new_name': new_name,
                    }
                }
            )
        except List.DoesNotExist:
            print('List does not exist:', list_id)


    async def delete_list(self, payload):
        list_id = payload['list_id']
        print('Deleting list:', list_id)

        try:
            # Fetch the list to be deleted
            task_list = await List.objects.aget(id=list_id)

            # Delete the list and its associated tasks
            await task_list.adelete()

            # Notify all clients in the board group about the deleted list
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'delete_list',
                    'payload': {
                        'list_id': list_id,
                    }
                }
            )
        except List.DoesNotExist:
            print('List does not exist:', list_id)

# =============================================  Board Methods =============================================

    async def update_board_name(self, payload):
        board_id = payload['board_id']
        new_name = payload['new_name']
        print('Updating board name:', board_id, new_name)

        try:
            board = await Board.objects.aget(id=board_id)

            board.name = new_name
            await board.asave()

            # Notify all clients in the board group about the updated board name
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'update_board_name',
                    'payload': {
                        'board_id': board_id,
                        'new_name': new_name,
                    }
                }
            )
        except Board.DoesNotExist:
            print('Board does not exist:', board_id)


    async def delete_board(self, payload):
        board_id = payload['board_id']
        user_id = payload['user_id']
        print('Deleting board:', board_id)

        if not await self.is_owner():
            print('user ownership:', self.scope['user'])
            print('Permission denied: Only the owner can delete the board.')
            return
        if  self.scope['user'].id != user_id:
            print('Permission denied: Only the owner can delete the board.')
            return
        try:
            # Fetch the board to be deleted
            board = await Board.objects.aget(id=board_id)
            # Delete the board and its associated lists and tasks
            await board.adelete()
            # Notify all clients in the board group about the deleted board
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'board_message',
                    'action': 'delete_board',
                    'payload': {
                        'board_id': board_id,
                    }
                }
            )
        except Board.DoesNotExist:
            print('Board does not exist:', board_id)
        except BoardMembership.DoesNotExist:
            print('Board membership does not exist:', board_id, self.scope['user'].id)
        except Exception as e:
            print('Error deleting board:', e)
            await self.send(text_data=json.dumps({
                'action': 'error',
                'message': str(e),
            }))


# =============================================  User Methods =============================================

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