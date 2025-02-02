import { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView();
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const sendMessage = async () => {
    try {
      const userMessage = { type: "user", content: message };
      setChatHistory((prev) => [...prev, userMessage]);
      setIsAiSpeaking(true);

      const response = await fetch("http://localhost:5001/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      if (data.responses) {
        const aiResponses = data.responses.map((content) => ({
          type: "ai",
          content,
        }));
        setChatHistory((prev) => [...prev, ...aiResponses]);
      }
      setMessage("");
      setIsAiSpeaking(false);
    } catch (error) {
      console.error("Error:", error);
      setIsAiSpeaking(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI Chatbot</h1>
        <div className="chat-container">
          <div className="ai-avatar-container">
            <div className={`ai-avatar ${isAiSpeaking ? "speaking" : ""}`}>
              <div className="avatar-circle">
                <div className="avatar-face">
                  <div className="avatar-eyes">
                    <div className="eye left"></div>
                    <div className="eye right"></div>
                  </div>
                  <div className="avatar-mouth"></div>
                </div>
              </div>
            </div>
          </div>
          <div className="messages">
            {chatHistory.map((msg, index) => (
              <div
                key={index}
                className={`message ${
                  msg.type === "user" ? "user-message" : "ai-message"
                }`}
              >
                <strong>{msg.type === "user" ? "You: " : "AI: "}</strong>
                {msg.content}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <div className="input-container">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) =>
                e.key === "Enter" && message.trim() && sendMessage()
              }
              placeholder="Type your message here..."
              className="input-field"
            />
            <button
              onClick={sendMessage}
              disabled={!message.trim()}
              className="send-button"
            >
              Send
            </button>
          </div>
        </div>
      </header>
    </div>
  );
}

export default App;
