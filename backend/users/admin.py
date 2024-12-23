from typing import Literal, Union

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import SafeText

from users.models import UserSubscriptions

User = get_user_model()


@admin.register(User)
class UserAdmin(UserAdmin):
    """
    Admin panel settings for the User model.
    """

    fieldsets = (
        (None, {'fields': ('avatar_preview', 'username', 'password')}),
        *UserAdmin.fieldsets[1:],
    )

    list_display = (
        'id',
        'avatar_preview',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('avatar_preview',)

    def avatar_preview(self, obj) -> Union[SafeText, Literal['']]:
        return obj.avatar_preview

    avatar_preview.short_description = 'Аватар'


@admin.register(UserSubscriptions)
class UserSubscriptionsAdmin(admin.ModelAdmin):
    """
    Admin panel settings for the UserSubscriptions model.
    """

    list_display = ('subscriber', 'subscribed_to')
    search_fields = ('subscriber__username', 'subscribed_to__username')


admin.site.unregister(Group)
