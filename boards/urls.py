from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, ListViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'boards', BoardViewSet)
router.register(r'lists', ListViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]




# sudo apt-get update
# sudo apt-get install redis-server


# sudo service redis-server start

# sudo service redis-server status

# sudo systemctl enable redis-server



# export DJANGO_SETTINGS_MODULE=taskmainder.settings
# daphne -b 0.0.0.0 -p 8000 taskmainder.asgi:application