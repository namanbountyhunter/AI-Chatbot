from django.urls import path
from .views import chat, stream_chat, create_session, get_sessions,get_messages,delete_session

urlpatterns = [
    path('chat/', chat),
    path('chat/stream/',stream_chat),
    path('session/', create_session),
    path('session/list/', get_sessions),
    path('session/<str:session_id>/', get_messages),
    path('session/delete/<int:session_id>/', delete_session)
]