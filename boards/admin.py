from django.contrib import admin
from .models import Board, BoardMembership , List, Task, BoardInvitation , Notification , PushSubscription
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class BoardAdminForm(forms.ModelForm):
    owner = forms.ModelChoiceField(queryset=User.objects.all(), required=True)

    class Meta:
        model = Board
        fields = ['name', 'owner']

    def save(self, commit=True):
        board = super().save(commit=False)
        if commit:
            board.save()
            BoardMembership.objects.create(board=board, user=self.cleaned_data['owner'], user_status='owner')
        return board

class BoardAdmin(admin.ModelAdmin):
    form = BoardAdminForm
    list_display = ('name', 'get_owner')

    def get_owner(self, obj):
        owner_membership = BoardMembership.objects.filter(board=obj, user_status='owner').first()
        return owner_membership.user if owner_membership else None
    get_owner.short_description = 'Owner'

class BoardMembershipAdmin(admin.ModelAdmin):
    list_display = ('board', 'user', 'user_status')
    list_filter = ('user_status',)
    search_fields = ('board__name', 'user__email')

admin.site.register(Board, BoardAdmin)
admin.site.register(BoardMembership, BoardMembershipAdmin)
admin.site.register(List)
admin.site.register(Task)
admin.site.register(BoardInvitation)
admin.site.register(Notification)
admin.site.register(PushSubscription)