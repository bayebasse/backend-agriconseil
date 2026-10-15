from django.urls import path
from .views import RegisterView, LoginView, LogoutView, MeView
urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="user-register"),
    path("auth/login/", LoginView.as_view(), name="user-login"),
    path("auth/logout/", LogoutView.as_view(), name="user-logout"),
    path("auth/me/", MeView.as_view(), name="user-me"),
]
