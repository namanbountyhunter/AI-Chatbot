from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import ChatSession, Message
from .serializers import ChatRequestSerializer, ChatResponseSerializer, ChatSessionSerializer
from .services.chat_service import ChatService
from django.http import StreamingHttpResponse


@api_view(["POST"])
def chat(request):
    request_serializer=ChatRequestSerializer(data=request.data)

    if not request_serializer.is_valid():
        return Response(request_serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    message=request_serializer.validated_data["message"]
    session_id=request_serializer.validated_data.get("session_id")

    
    service=ChatService()
    reply,session_id=service.process_message(message,session_id)
        
    response_data=({
            "reply":reply,
            "session_id":session_id
        })
    response_serializer=ChatResponseSerializer(data=response_data)
        
    response_serializer.is_valid(raise_exception=True)
    
    return Response(response_serializer.data)

from .models import ChatSession, Message

@api_view(['POST'])
def stream_chat(request):
    message = request.data.get("message")
    session_id = request.data.get("session_id")

    service = ChatService()

    # ✅ Get session
    session = ChatSession.objects.get(id=session_id)

    # ✅ Save user message
    Message.objects.create(
        session=session,
        role="user",
        content=message
    )

    def generate():
        full_response = ""

        for chunk in service.stream_message(message, session_id):
            full_response += chunk
            yield chunk

        Message.objects.create(
            session=session,
            role="bot",
            content=full_response
        )

    return StreamingHttpResponse(generate(), content_type="text/plain")

@api_view(['POST'])
def create_session(request):
    session=ChatSession.objects.create()
    return Response({'session_id':session.id})

@api_view(['GET'])
def get_sessions(request):
    sessions = ChatSession.objects.all().order_by('-created_at')
    serializer = ChatSessionSerializer(sessions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_messages(request, session_id):
    messages = Message.objects.filter(session_id=session_id).order_by('created_at')
    data = [
        {"role": m.role, "text": m.content}
        for m in messages
    ]
    return Response(data)

@api_view(['DELETE'])
def delete_session(request, session_id):
    try:
        session = ChatSession.objects.get(id=session_id)
        session.delete()
        return Response({"message": "Deleted successfully"})
    except ChatSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)



        