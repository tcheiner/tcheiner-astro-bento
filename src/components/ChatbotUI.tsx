import React, { useState } from 'react';

const ChatbotUI = () => {
  const [isOpen, setIsOpen] = useState(false); // Toggle chatbot open/close
  const [messages, setMessages] = useState([]); // Chat messages
  const [input, setInput] = useState(""); // User input

  const toggleChatbot = () => setIsOpen(!isOpen);

  // const sendMessage = () => {
  //   if (!input.trim()) return;
  //
  //   // Add user message
  //   setMessages((prev) => [...prev, { sender: "user", text: input }]);
  //
  //   // Simulate bot response
  //   setTimeout(() => {
  //     setMessages((prev) => [...prev, { sender: "bot", text: `You said: "${input}"` }]);
  //   }, 500);
  //
  //   setInput(""); // Clear input
  // };

  const sendMessage = async () => {
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: input }),
    });
    const data = await response.json();
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: input },
      { sender: "bot", text: data.answer },
    ]);
    setInput("");
  };

  return (
    <>
      {!isOpen && (
        <button
          onClick={toggleChatbot}
          className="fixed bottom-4 right-4 bg-yellow-600 bg-opacity-60 text-white p-4 rounded-full shadow-lg hover:bg-opacity-100 focus:outline-none"
        >
          💬 Chat
        </button>
      )}

      {isOpen && (
        <div className="fixed bottom-20 right-4 w-80 bg-white shadow-lg rounded-lg border border-gray-200">
          <div className="bg-yellow-600 text-white p-3 flex justify-between items-center rounded-t-lg">
            <h3 className="font-bold">Chatbot</h3>
            <button onClick={toggleChatbot}>✖</button>
          </div>
          <div className="p-3 h-64 overflow-y-auto">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-sm text-center">Say hi to start the conversation!</p>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={index}
                  className={`mb-2 ${msg.sender === "user" ? "text-right" : "text-left"}`}
                >
                  <span
                    className={`inline-block px-3 py-2 rounded-lg ${
                      msg.sender === "user"
                        ? "bg-yellow-500 text-white"
                        : "bg-gray-200 text-black"
                    }`}
                  >
                    {msg.text}
                  </span>
                </div>
              ))
            )}
          </div>
          <div className="p-3 border-t border-gray-200 flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring focus:ring-blue-300"
            />
            <button
              onClick={sendMessage}
              className="ml-2 bg-yellow-600 text-white px-3 py-2 rounded-lg hover:bg-yellow-500 focus:outline-none"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatbotUI;
