from django.db import models
from django.conf import settings



class Board(models.Model):
  name = models.CharField(max_length=255)
  owner = models.ForeignKey(settings.AUTH_USER_MODEL  , related_name='boards' , on_delete=models.CASCADE)
  created_at = models.DateField(auto_now_add=True)

  def __str__(self):
    return self.name
  


class List(models.Model):
  name= models.CharField(max_length=255)
  board = models.ForeignKey(Board, related_name='lists', on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.name
  


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    list = models.ForeignKey(List, related_name='tasks', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title
















