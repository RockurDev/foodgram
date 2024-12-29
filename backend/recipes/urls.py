from django.urls import path

from .views import redirect_short_url

urlpatterns = [
    path('s/<str:short_url>/', redirect_short_url, name='redirect_short_url'),
]
