from django.urls import path

from .admin_views import (
    AdminFarmerCultureCreateView,
    AdminFarmerDetailView,
    AdminFarmerListCreateView,
)


urlpatterns = [
    path(
        "agriculteurs/",
        AdminFarmerListCreateView.as_view(),
        name="admin-agriculteurs",
    ),

    path(
        "agriculteurs/<int:pk>/",
        AdminFarmerDetailView.as_view(),
        name="admin-agriculteur-detail",
    ),

    path(
        "agriculteurs/<int:pk>/cultures/",
        AdminFarmerCultureCreateView.as_view(),
        name="admin-agriculteur-culture-create",
    ),
]