from django.core.management.base import BaseCommand
from boards.models import PushSubscription
from pywebpush import webpush, WebPushException
import json

class Command(BaseCommand):
    help = 'Send a test push notification to a user'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='The ID of the user to send the notification to')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        subscriptions = PushSubscription.objects.filter(user_id=user_id)

        if not subscriptions.exists():
            self.stdout.write(self.style.ERROR('No subscriptions found for this user.'))
            return

        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info=subscription.subscription_info,
                    data=json.dumps({
                        'title': 'Test Notification',
                        'body': 'This is a test push notification!',
                    }),
                    vapid_private_key='4aMg0XhG2sXL0LAftafusC0jpOorGDb8efcyxsCNjvw',  
                    vapid_claims={
                        'sub': 'mailto:your-email@example.com' 
                    }
                )
                self.stdout.write(self.style.SUCCESS('Test notification sent successfully!'))
            except WebPushException as e:
                self.stdout.write(self.style.ERROR(f"Web push failed: {e}"))