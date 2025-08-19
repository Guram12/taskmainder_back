from django.contrib import admin
from django.urls import path , include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('acc/', include('accounts.urls')),
    path('api/', include('boards.urls')),
]
