from chatbot.models import ChatSession, Message
from .ollama_client import OllamaClient
from django.core.exceptions import ObjectDoesNotExist
import logging
import time

logger = logging.getLogger("chatbot")


class ChatService:

    SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful AI assistant.\n"
        "- Always answer ONLY the latest user question.\n"
        "- Do NOT continue previous topics.\n"
        "- Keep answers short (2-3 sentences).\n"
        "- Do NOT ask follow-up questions.\n"
        "- Be clear and direct.\n"
    ),
}

    def __init__(self, model="phi3"):
        self.client = OllamaClient(model=model)

    # =========================
    # MAIN ENTRY
    # =========================
    def process_message(self, user_message, session_id=None):

        user_message = user_message.strip()
        message_lower = user_message.lower()

        # 🔹 Greeting shortcut (fast path)
        if message_lower in ["hi", "hello", "hey", "hii", "yo"]:
            session = self._get_or_create_session(session_id)
            if not session.title:
              session.title = user_message.strip().capitalize()[:30]
              session.save()

            reply = "Hey! What do you need help with?"

            self._save_message(session, "user", user_message)
            self._save_message(session, "assistant", reply)

            return reply, str(session.id)

        start_time = time.time()

        logger.info(
            f"Processing message | session_id={session_id} | length={len(user_message)}"
        )

        # 1️⃣ Session
        session = self._get_or_create_session(session_id)
        if not session.title:
           session.title = user_message.strip().capitalize()[:30]
           session.save()

        # 2️⃣ Save user message
        self._save_message(session, "user", user_message)

        # 3️⃣ Build history
        history = self._build_history(session)

        # 4️⃣ Call model
        ollama_start = time.time()

        reply = self.client.chat(history)
        reply = reply.replace("Assistant:", "").strip()
        
        reply = reply.split(".")[:2]
        reply = ".".join(reply).strip()

        if not reply.endswith("."):
          reply += "."

        ollama_time = time.time() - ollama_start

        logger.info(
            f"Ollama response time={ollama_time:.2f}s | session_id={session.id}"
        )

        # 5️⃣ Save assistant reply
        self._save_message(session, "assistant", reply)

        # 6️⃣ Optional summary update
        if Message.objects.filter(session=session).count() % 10 == 0:
            self._update_summary(session)

        total_time = time.time() - start_time

        logger.info(
            f"Total processing time={total_time:.2f}s | session_id={session.id}"
        )

        return reply, str(session.id)

    # =========================
    # STREAMING (IMPORTANT)
    # =========================
    def stream_message(self, user_message, session_id=None):

        user_message = user_message.strip()

        session = self._get_or_create_session(session_id)

        # Save user message
        self._save_message(session, "user", user_message)

        history = self._build_history(session)

        full_reply = ""

        try:
            for chunk in self.client.chat_stream(history):

                # 🔥 clean chunk BEFORE sending
                chunk = chunk.replace("Assistant:", "")

                full_reply += chunk
                yield chunk

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield "Error generating response"
            return

        full_reply = full_reply.strip()

        # Save assistant response
        self._save_message(session, "assistant", full_reply)

        # Update summary occasionally
        if Message.objects.filter(session=session).count() % 10 == 0:
            self._update_summary(session)

    # =========================
    # HISTORY BUILDER (SMART)
    # =========================
    def _build_history(self, session):

        # 🔥 Only last 5 messages (fast + effective)
        last_messages = (
            Message.objects
            .filter(session=session)
            .order_by("-created_at")[:3]
        )

        last_messages = list(reversed(last_messages))

        history = [self.SYSTEM_PROMPT]

        # 🔹 Add summary if exists
        if session.summary:
            history.append({
                "role": "system",
                "content": session.summary.replace("user:", "").replace("assistant:", "").strip()
            })

        for msg in last_messages:
            history.append({
                "role": msg.role,
                "content": msg.content.strip()
            })

        return history

    # =========================
    # SESSION HANDLING
    # =========================
    def _get_or_create_session(self, session_id):
        if session_id:
            try:
                return ChatSession.objects.get(id=session_id)
            except ObjectDoesNotExist:
                return ChatSession.objects.create()
        return ChatSession.objects.create()

    # =========================
    # SAVE MESSAGE
    # =========================
    def _save_message(self, session, role, content):
        Message.objects.create(
            session=session,
            role=role,
            content=content
        )

    # =========================
    # SUMMARY (FIXED)
    # =========================
    def _update_summary(self, session):

        messages = Message.objects.filter(session=session).order_by("created_at")

        if not messages.exists():
            return

        text = ""
        for msg in messages:
            text += f"{msg.role}: {msg.content}\n"

        prompt = [
            {
                "role": "system",
                "content": (
                    "Summarize the conversation briefly, keeping key facts like names, "
                    "preferences, and important context."
                )
            },
            {
                "role": "user",
                "content": text
            }
        ]

        try:
            summary = self.client.chat(prompt)
            session.summary = summary.strip()
            session.save()

        except Exception as e:
            logger.error(f"Summary error: {e}")