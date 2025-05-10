from django.db import models
from django.conf import settings

from .tasks import send_task_due_email
from django.utils.timezone import is_naive, make_aware


class Board(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateField(auto_now_add=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='BoardMembership',
        related_name='boards_members',
        blank=True
    )

    def __str__(self):
        return self.name

class BoardMembership(models.Model):
    USER_STATUS_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    user_status = models.CharField(max_length=10, choices=USER_STATUS_CHOICES)

    class Meta:
        unique_together = ('user', 'board')

    def __str__(self):
        return f"{self.user.email} - {self.board.name} - {self.user_status}"
    
    

class List(models.Model):
    name= models.CharField(max_length=255)
    board = models.ForeignKey(Board, related_name='lists', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
  
    def get_sorted_tasks(self):
        return self.tasks.order_by('order') 

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    list = models.ForeignKey(List, related_name='tasks', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0) 
    task_associated_users_id = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='associated_tasks', blank=True)




    class Meta:
        ordering = ['order'] 

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Debug the due_date time zone
        print(f"Original due_date: {self.due_date}")
        if self.due_date and is_naive(self.due_date):
            self.due_date = make_aware(self.due_date)
        print(f"Converted due_date to UTC: {self.due_date}")

        super().save(*args, **kwargs)

        # Schedule email notifications for associated users
        if self.due_date:
            for user in self.task_associated_users_id.all():
                print(f"Scheduling email for {user.email} at {self.due_date} (UTC)")
                send_task_due_email.apply_async(
                    args=[user.email, self.title, self.due_date.isoformat()],
                    eta=self.due_date
                )
            super().save(*args, **kwargs)




