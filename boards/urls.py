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