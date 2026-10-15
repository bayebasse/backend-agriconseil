from django.urls import path
from .views import AgriculturalChatView, AnalyzePhotoView, ChatbotView, PhotoListView
urlpatterns = [
    path("ia/analyse/", AnalyzePhotoView.as_view()),
    path("ia/historique/", PhotoListView.as_view()),
    path("ia/chat/", AgriculturalChatView.as_view(), name="agricultural-chat"),
    path("chatbot/", ChatbotView.as_view(), name="chatbot"),
]
