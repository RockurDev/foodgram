from django.contrib import admin

from users.models import User, UserSubscriptions


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Admin panel settings for the User model.
    """

    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(UserSubscriptions)
class UserSubscriptionsAdmin(admin.ModelAdmin):
    """
    Admin panel settings for the UserSubscriptions model.
    """

    list_display = ('subscriber', 'subscribed_to')
    search_fields = ('subscriber__username', 'subscribed_to__username')
