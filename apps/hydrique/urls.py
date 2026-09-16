from django.urls import path
from .views import HydricView
urlpatterns = [path("hydrique/<int:culture_id>/", HydricView.as_view())]
