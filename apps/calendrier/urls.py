from django.urls import path
from .views import CalendrierDetailView, StadeView
urlpatterns = [path("calendriers/<int:culture_id>/", CalendrierDetailView.as_view()), path("cultures/<int:culture_id>/stade/", StadeView.as_view())]
