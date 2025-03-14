from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user(token):
    try:
        # Decode the token to get the user ID
        untoken = UntypedToken(token)
        user_id = untoken['user_id']
        print(f"Decoded user_id: {user_id}")
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError) as e:
        print(f"Token error: {e}")
        return AnonymousUser()
    except User.DoesNotExist:
        print("User does not exist")
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope['query_string'].decode())
        token = query_string.get('token')
        if token:
            print(f"Token received: {token[0]}")
            scope['user'] = await get_user(token[0])
        else:
            print("No token found")
            scope['user'] = AnonymousUser()
        return await super().__call__(scope, receive, send)