from django.urls import path

from .social_views import GoogleLoginView

urlpatterns = [
    path('', GoogleLoginView.as_view(), name='google_login'),
]
