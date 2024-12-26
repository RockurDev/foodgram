from django.views import View
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsAuthorOrReadOnly(BasePermission):
    """
    Custom permission to allow read-only access
    to an object or full access to the author.
    """

    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        return request.method in SAFE_METHODS or obj.author == request.user
