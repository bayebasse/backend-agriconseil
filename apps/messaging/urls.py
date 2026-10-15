from django.urls import path

from .views import (
    ConversationListView,
    ConversationMessagesView,
    MessageAudioView,
    StartConversationView,
)


urlpatterns = [
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/from-crop/<int:culture_id>/", StartConversationView.as_view(), name="conversation-from-crop"),
    path("conversations/<int:conversation_id>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
    path("<int:message_id>/audio/", MessageAudioView.as_view(), name="message-audio"),
]
