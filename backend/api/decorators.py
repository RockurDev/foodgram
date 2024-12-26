from functools import wraps

from django.db.models import QuerySet
from rest_framework.response import Response


def paginate(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Response:
        queryset = func(self, *args, **kwargs)
        assert isinstance(
            queryset, (list, QuerySet)
        ), 'apply_pagination expects a List or a QuerySet'

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    return wrapper
