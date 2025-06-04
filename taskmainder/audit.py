import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict

@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if sender._meta.app_label in ["boards", "accounts"]:  # add all your app names here
        data = {
            "action": "created" if created else "updated",
            "model": sender.__name__,
            "instance": model_to_dict(instance),
            "timestamp": str(instance._state.db),
        }
        with open('audit_logs.json', 'a') as f:
            f.write(json.dumps(data) + "\n")

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender._meta.app_label in ["boards", "accounts"]:
        data = {
            "action": "deleted",
            "model": sender.__name__,
            "instance": model_to_dict(instance),
            "timestamp": str(instance._state.db),
        }
        with open('audit_logs.json', 'a') as f:
            f.write(json.dumps(data) + "\n")
