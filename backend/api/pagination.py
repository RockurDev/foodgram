from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """
    Custom pagination class to set a default page size
    and allow dynamic page size
    through a query parameter with a maximum limit.
    """

    page_size = settings.PAGINATION_PAGE_SIZE
    page_size_query_param = settings.PAGINATION_PAGE_SIZE_QUERY_PARAM
    max_page_size = settings.PAGINATION_MAX_PAGE_SIZE
