import React, { useState, useRef, useEffect } from "react";
import Message from "./components/Message";

function App() {
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // =========================
  // FETCH SESSIONS
  // =========================
  const fetchSessions = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/session/list/");
      const data = await res.json();
      setSessions(data);
    } catch (err) {
      console.error("Session fetch error:", err);
    }
  };

  // =========================
  // CREATE NEW CHAT
  // =========================
  const createNewChat = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/session/", {
        method: "POST",
      });

      const data = await res.json();

      setCurrentSession(data.session_id);

      // 🔥 instant welcome message (no delay)
      setMessages([
        {
          role: "assistant",
          text: "",
        },
      ]);

      // typing effect
      const welcome = "Hey! What do you need help with?";
      let i = 0;

      const interval = setInterval(() => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[0] = {
            ...updated[0],
            text: welcome.slice(0, i),
          };
          return updated;
        });

        i++;
        if (i > welcome.length) clearInterval(interval);
      }, 15);

      fetchSessions();
    } catch (err) {
      console.error("Create session error:", err);
    }
  };

  // =========================
  // INIT
  // =========================
  useEffect(() => {
    fetchSessions();
    createNewChat();
  }, []);

  // =========================
  // LOAD MESSAGES
  // =========================
  useEffect(() => {
    if (!currentSession) return;

    const loadMessages = async () => {
      try {
        const res = await fetch(
          `http://127.0.0.1:8000/api/session/${currentSession}/`
        );
        const data = await res.json();

        // if empty, keep welcome message
        if (data.length > 0) {
          setMessages(data);
        }
      } catch (err) {
        console.error("Load messages error:", err);
      }
    };

    loadMessages();
  }, [currentSession]);

  // =========================
  // AUTO SCROLL
  // =========================
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // =========================
  // AUTO FOCUS INPUT
  // =========================
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // =========================
  // SEND MESSAGE (STREAMING)
  // =========================
  const sendMessage = async () => {
    if (!input.trim() || loading || !currentSession) return;

    const userText = input;

    const userMessage = { role: "user", text: userText };

    setMessages((prev) => [
      ...prev,
      userMessage,
      { role: "assistant", text: "" },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/chat/stream/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: userText,
            session_id: currentSession,
          }),
        }
      );

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let botMessage = "";
      let lastUpdate = Date.now();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // 🔥 FIXED decoding
        const chunk = decoder.decode(value, { stream: true });

        botMessage += chunk;

        // 🔥 throttle updates
        if (Date.now() - lastUpdate > 50) {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              text: botMessage + "▌",
            };
            return updated;
          });
          lastUpdate = Date.now();
        }
      }

      // final update (remove cursor)
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          text: botMessage,
        };
        return updated;
      });

    } catch (error) {
      console.error(error);

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          text: "⚠️ Error connecting to server",
        };
        return updated;
      });
    }

    setLoading(false);
  };

  return (
    <div style={{ display: "flex", height: "100vh", color: "white" }}>

      {/* SIDEBAR */}
      <div style={{
        width: "250px",
        background: "#202123",
        padding: "10px",
        display: "flex",
        flexDirection: "column"
      }}>

        <button
          onClick={createNewChat}
          style={{
            padding: "10px",
            marginBottom: "10px",
            background: "#444654",
            color: "white",
            border: "none",
            cursor: "pointer"
          }}
        >
          + New Chat
        </button>

        <div style={{ overflowY: "auto", flex: 1 }}>
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => setCurrentSession(s.id)}
              style={{
                padding: "10px",
                cursor: "pointer",
                background:
                  currentSession === s.id ? "#444654" : "transparent"
              }}
            >
              Chat {s.id}
            </div>
          ))}
        </div>
      </div>

      {/* MAIN CHAT */}
      <div style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        background: "#343541"
      }}>

        {/* HEADER */}
        <div style={{
          padding: "15px",
          borderBottom: "1px solid #555",
          textAlign: "center",
          fontWeight: "bold"
        }}>
          AI Chatbot
        </div>

        {/* CHAT */}
        <div style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px",
          display: "flex",
          flexDirection: "column",
          gap: "10px"
        }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              display: "flex",
              justifyContent:
                msg.role === "user" ? "flex-end" : "flex-start"
            }}>
              <div style={{
                padding: "12px 16px",
                borderRadius: "18px",
                maxWidth: "60%",
                background:
                  msg.role === "user" ? "#0b93f6" : "#444654",
                whiteSpace: "pre-wrap"
              }}>
                <Message role={msg.role} content={msg.text} />
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ color: "#aaa" }}>Assistant is typing...</div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* INPUT */}
        <div style={{
          padding: "15px",
          borderTop: "1px solid #555"
        }}>
          <div style={{
            display: "flex",
            maxWidth: "800px",
            margin: "0 auto",
            background: "#40414f",
            borderRadius: "10px"
          }}>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Send a message..."
              style={{
                flex: 1,
                padding: "12px",
                border: "none",
                outline: "none",
                background: "transparent",
                color: "white"
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading) sendMessage();
              }}
            />

            <button
              onClick={sendMessage}
              disabled={loading || !currentSession}
              style={{
                padding: "10px 16px",
                background: "#0b93f6",
                border: "none",
                color: "white",
                cursor: "pointer",
                opacity: loading ? 0.6 : 1
              }}
            >
              Send
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;