from django.urls import path
from .views import AnalyzePhotoView, PhotoListView
urlpatterns = [path("ia/analyse/", AnalyzePhotoView.as_view()), path("ia/historique/", PhotoListView.as_view())]
