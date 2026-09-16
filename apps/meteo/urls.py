from django.urls import path
from .views import MeteoCultureView
urlpatterns = [path("meteo/<int:culture_id>/", MeteoCultureView.as_view())]
