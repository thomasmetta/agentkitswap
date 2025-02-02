import { useState } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [responses, setResponses] = useState([]);

  const sendMessage = async () => {
    try {
      const response = await fetch("http://localhost:5001/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      if (data.responses) {
        setResponses((prev) => [...prev, ...data.responses]);
      }
      setMessage(""); // Clear input after sending
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI Chatbot</h1>
        <div className="chat-container">
          <div className="messages">
            {responses.map((response, index) => (
              <p key={index} className="message">
                {response}
              </p>
            ))}
          </div>
          <div className="input-container">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Type your message..."
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      </header>
    </div>
  );
}

export default App;
