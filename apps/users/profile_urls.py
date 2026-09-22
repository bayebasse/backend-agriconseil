from django.urls import path

from .profile_views import ProfileView


urlpatterns = [
    path(
        "",
        ProfileView.as_view(),
        name="profile",
    ),
]