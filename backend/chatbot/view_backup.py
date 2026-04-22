import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import ChatSession, Message


@api_view(["POST"])
def chat(request):
    user_message = request.data.get("message")
    session_id = request.data.get("session_id")

    if not user_message:
        return Response({"error": "Message is required"}, status=400)

    # Get or create session
    if session_id:
        session = ChatSession.objects.get(id=session_id)
    else:
        session = ChatSession.objects.create()

    # Save user message
    Message.objects.create(
        session=session,
        role="user",
        content=user_message
    )

    # Get last 10 messages (correct order)
    messages = (
        Message.objects
        .filter(session=session)
        .order_by("-created_at")[:10]
    )

    # Reverse them to chronological order
    messages = list(messages)[::-1]

    # Convert to Ollama chat format
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "mistral",
                "messages": chat_history,
                "stream": False
            },
            timeout=120
        )

        data = response.json()

        # Ollama chat response format
        ai_reply = data["message"]["content"]

        # Save assistant reply
        Message.objects.create(
            session=session,
            role="assistant",
            content=ai_reply
        )

        return Response({
            "reply": ai_reply,
            "session_id": session.id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)