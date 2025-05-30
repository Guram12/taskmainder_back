from django.contrib import admin
from .models import Board, BoardMembership , List, Task, BoardInvitation , Notification , PushSubscription
from django import forms



class BoardMembershipAdmin(admin.ModelAdmin):
    list_display = ('board', 'user', 'user_status')
    list_filter = ('user_status',)
    search_fields = ('board__name', 'user__email')


class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')  # Display name and creation date in the admin list view
    search_fields = ('name',)  # Allow searching by board name
    list_filter = ('created_at',)  # Filter boards by creation date
    readonly_fields = ('created_at',)  # Make the created_at field read-only
    fields = ('name', 'background_image', 'created_at')  # Specify fields to display in the admin form

admin.site.register(Board, BoardAdmin)
admin.site.register(BoardMembership, BoardMembershipAdmin)
admin.site.register(List)
admin.site.register(Task)
admin.site.register(BoardInvitation)
admin.site.register(Notification)
admin.site.register(PushSubscription)