from django.db import models
from django.conf import settings
from django.utils.timezone import now
from .tasks import send_task_due_email
from django.utils.timezone import is_naive, make_aware

# ===============================================================================================

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

# ===============================================================================================

class BoardMembership(models.Model):
    USER_STATUS_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    user_status = models.CharField(max_length=10, choices=USER_STATUS_CHOICES)
    is_invitation_accepted = models.BooleanField(default=False) 

    class Meta:
        unique_together = ('user', 'board')

    def __str__(self):
        return f"{self.user.email} - {self.board.name} - {self.user_status}"


# ===============================================================================================


class BoardInvitation(models.Model):
    email = models.EmailField()
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation to {self.email} for board {self.board.name}"



# ===============================================================================================


class List(models.Model):
    name= models.CharField(max_length=255)
    board = models.ForeignKey(Board, related_name='lists', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
  
    def get_sorted_tasks(self):
        return self.tasks.order_by('order') 
# ===============================================================================================

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    list = models.ForeignKey(List, related_name='tasks', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0) 
    task_associated_users_id = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='associated_tasks', blank=True)

    PRIORITY_CHOICES = [
        ('green', 'Green'),
        ('orange', 'Orange'),
        ('red', 'Red'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, blank=True, null=True, default=None)  # New field



    class Meta:
        ordering = ['order'] 

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.pk:  # If the task already exists
            original_task = Task.objects.filter(pk=self.pk).first()
            if original_task:
                if original_task.list != self.list:
                    print(f"Task moved from list '{original_task.list}' to list '{self.list}'. Skipping email scheduling.")
                    # Save the task even if the list changes
                    super().save(*args, **kwargs)
                    return

                if original_task.due_date != self.due_date:
                    if self.due_date and is_naive(self.due_date):
                        self.due_date = make_aware(self.due_date)
                    if self.due_date and self.due_date > now():
                        # Save the task before scheduling emails
                        super().save(*args, **kwargs)
                        for user in self.task_associated_users_id.all():
                            print(f"Scheduling email for {user.email} at {self.due_date} (UTC)")
                            send_task_due_email.apply_async(
                                args=[self.id, user.email, user.username, self.title, self.due_date.isoformat(), self.priority],
                                eta=self.due_date
                            )
                        return

        # Ensure the task is saved in all other cases
        if self.due_date and self.due_date > now():
            if is_naive(self.due_date):
                self.due_date = make_aware(self.due_date)
        super().save(*args, **kwargs)

        # Schedule emails if the task is new and has a valid due date
        if self.due_date and self.due_date > now() and self.task_associated_users_id.exists():
            for user in self.task_associated_users_id.all():
                print(f"Scheduling email for {user.email} at {self.due_date} (UTC)")
                send_task_due_email.apply_async(
                    args=[self.id, user.email, user.username, self.title, self.due_date.isoformat(), self.priority],
                    eta=self.due_date
                )


# ============================================== push notification ========================================================


# filepath: /home/guram/Desktop/task_management_app/task_back/taskmainder/boards/models.py
class PushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription_info = models.JSONField()

    class Meta:
        unique_together = ('user',)