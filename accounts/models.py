from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf  import settings
import pytz


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/profile_pictures/user_<id>/<filename>
    return f'profile_pictures/user_{instance.email}/{filename}'



class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True , blank=True , null=True)
    phone_number = models.CharField(max_length=25, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to=user_directory_path, 
        blank=True, 
        null=True, 
    )    
    is_email_verified = models.BooleanField(default=False)  
    timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones], default='UTC', blank=True, null=True)
    is_social_account = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email


    def save(self, *args, **kwargs):
        try:
            this = CustomUser.objects.get(id=self.id)
            if this.profile_picture != self.profile_picture and this.profile_picture:
                this.profile_picture.delete(save=False)
        except CustomUser.DoesNotExist:
            pass

        # Set profile_picture to None if not provided
        if not self.profile_picture:
            self.profile_picture = None

        super(CustomUser, self).save(*args, **kwargs)









