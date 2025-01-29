from django.core.management.base import BaseCommand
from faker import Faker
from accounts.models import CustomUser
from boards.models import Board, List, Task

class Command(BaseCommand):
    help = 'Generate fake data for boards, lists, and tasks'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Create a user
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='password123'
        )

        # Create 2 boards
        for _ in range(2):
            board = Board.objects.create(
                name=fake.word(),
                owner=user
            )

            # Create 3 lists for each board
            for _ in range(3):
                list_obj = List.objects.create(
                    name=fake.word(),
                    board=board
                )

                # Create 5 tasks for each list
                for _ in range(5):
                    Task.objects.create(
                        title=fake.sentence(),
                        description=fake.text(),
                        list=list_obj,
                        due_date=fake.future_datetime()
                    )

        self.stdout.write(self.style.SUCCESS('Successfully generated fake data'))