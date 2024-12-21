from rest_framework.pagination import PageNumberPagination

from .constants import (
    PAGINATION_MAX_PAGE_SIZE,
    PAGINATION_PAGE_SIZE,
    PAGINATION_PAGE_SIZE_QUERY_PARAM,
)


class DefaultPagintaion(PageNumberPagination):
    """
    Custom pagination class to set a default page size
    and allow dynamic page size
    through a query parameter with a maximum limit.
    """

    page_size = PAGINATION_PAGE_SIZE
    page_size_query_param = PAGINATION_PAGE_SIZE_QUERY_PARAM
    max_page_size = PAGINATION_MAX_PAGE_SIZE
