from django.urls import path

from .views import redirect_short_url

urlpatterns = [
    path('<str:short_url>/', redirect_short_url, name='redirect_short_url'),
]
