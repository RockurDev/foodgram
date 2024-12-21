from django.views import View

from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request


class MeOnlyForAuthenticatedUsers(permissions.BasePermission):
    """
    Custom permission to allow access to '/me/' endpoint
    only for authenticated users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        if '/me/' in request.get_full_path():
            return request.user.is_authenticated
        return True


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access
    to an object or full access to the author.
    """

    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        return request.method in SAFE_METHODS or obj.author == request.user
