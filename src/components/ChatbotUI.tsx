import React, { useState } from 'react';

type Message = { sender: "user" | "bot"; text: string };

const ChatbotUI = () => {
  const [isOpen, setIsOpen] = useState(false); // Toggle chatbot open/close
  const [messages, setMessages] = useState<Message[]>([]); // Chat messages
  const [input, setInput] = useState(""); // User input
  const [isExpanded, setIsExpanded] = useState(false); // Track if chatbot should be expanded
  const [questionsUsed, setQuestionsUsed] = useState(0); // Track free questions used
  const [userApiKey, setUserApiKey] = useState(""); // User's own API key
  const [showApiKeyInput, setShowApiKeyInput] = useState(false); // Show API key input

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
    if (!input.trim()) return; // Don't send empty messages

    // Check if user has exceeded free questions and no API key provided
    if (questionsUsed >= 5 && !userApiKey) {
      setShowApiKeyInput(true);
      setMessages((prev) => [...prev,
        { sender: "user", text: input.trim() },
        { sender: "bot", text: "You've used your 5 free questions! To continue asking about my experience and projects, please provide your own OpenAI API key below." }
      ]);
      setInput("");
      return;
    }

    const apiUrl = import.meta.env.PUBLIC_CHATBOT_API_URL;
    const userMessage = input.trim();

    // Expand chatbot on first message
    if (messages.length === 0) {
      setIsExpanded(true);
    }

    // Add user message immediately
    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);
    setInput(""); // Clear input immediately

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMessage,
          userApiKey: userApiKey || undefined
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const data = await response.json();

      // Increment question count only if using free questions
      if (!userApiKey) {
        setQuestionsUsed(prev => prev + 1);
      }

      setMessages((prev) => [...prev, { sender: "bot", text: data.answer }]);

      // Show warning when approaching limit
      if (!userApiKey && questionsUsed === 3) {
        setMessages((prev) => [...prev, {
          sender: "bot",
          text: "⚠️ You have 1 free question remaining. After that, you'll need to provide your own OpenAI API key to continue."
        }]);
      }

    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, I encountered an error processing your question. Please try again." }
      ]);
    }
  };

  return (
    <>
      {/* Blur backdrop when expanded */}
      {isOpen && isExpanded && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-40"
          onClick={() => setIsExpanded(false)}
        />
      )}

      {!isOpen && (
        <button
          onClick={toggleChatbot}
          className="fixed bottom-4 right-4 bg-yellow-600 bg-opacity-60 text-white p-4 rounded-full shadow-lg hover:bg-opacity-100 focus:outline-none z-50"
        >
          💬 Chat
        </button>
      )}

      {isOpen && (
        <div className={`fixed bg-white shadow-lg rounded-lg border border-gray-200 z-50 transition-all duration-300 flex flex-col ${
          isExpanded
            ? 'top-16 right-8 bottom-16 w-[550px] max-w-[70vw]' // Expanded: 40% wider total (384px -> 550px, 50vw -> 70vw)
            : 'bottom-20 right-4 w-[460px] h-auto' // Compact: 40% wider total (320px -> 460px)
        }`}>
          <div className="bg-yellow-600 text-white p-3 flex justify-between items-center rounded-t-lg">
            <h3 className="font-bold text-sm">TC Heiner - Ask me anything!</h3>
            <div className="flex gap-2">
              {isExpanded && (
                <button
                  onClick={() => setIsExpanded(false)}
                  className="hover:bg-yellow-700 px-2 py-1 rounded text-sm"
                  title="Minimize"
                >
                  ⊟
                </button>
              )}
              <button onClick={toggleChatbot} title="Close">✖</button>
            </div>
          </div>
          <div className={`flex-1 overflow-hidden ${
            isExpanded ? 'py-[15%] px-4' : 'p-3'
          }`}>
            <div className={`w-full h-full overflow-y-auto ${
              isExpanded ? '' : 'h-64'
            }`}>
              {messages.length === 0 ? (
                <div className="text-gray-600 text-sm text-center space-y-3 p-3">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="font-semibold text-blue-800 mb-2">👋 Hi! I'm TC Heiner</p>
                    <p className="text-blue-700">Ask me questions about my experiences and past projects here.</p>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="font-semibold text-green-800 mb-1">🎁 Free Questions</p>
                    <p className="text-green-700">You get <strong>5 free questions</strong> powered by GPT-4o-mini about me and my work.</p>
                    <p className="text-green-600 text-xs mt-1">After that, you can use your own OpenAI API key to continue.</p>
                  </div>
                  <p className="text-gray-500 text-xs">Questions remaining: <strong>{5 - questionsUsed}</strong></p>
                </div>
              ) : (
                <div className="p-3">
                  {messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`mb-3 ${msg.sender === "user" ? "text-right" : "text-left"}`}
                    >
                      <span
                        className={`inline-block px-3 py-2 rounded-lg text-xs leading-relaxed max-w-[85%] ${
                          msg.sender === "user"
                            ? "bg-yellow-500 text-white"
                            : "bg-gray-200 text-black whitespace-pre-line"
                        }`}
                      >
                        {msg.sender === "bot" ? (
                          <span dangerouslySetInnerHTML={{ __html: msg.text }} />
                        ) : (
                          msg.text
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className={`border-t border-gray-200 ${
            isExpanded ? 'absolute bottom-0 left-0 right-0 p-4' : 'p-3'
          }`}>
            {/* API Key Input */}
            {showApiKeyInput && (
              <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800 mb-2">🔑 Enter your OpenAI API Key to continue:</p>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={userApiKey}
                    onChange={(e) => setUserApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="flex-1 px-3 py-2 text-sm border border-yellow-300 rounded-lg focus:outline-none focus:ring focus:ring-yellow-300"
                  />
                  <button
                    onClick={() => setShowApiKeyInput(false)}
                    className="bg-yellow-600 text-white px-3 py-2 text-sm rounded-lg hover:bg-yellow-500 focus:outline-none"
                  >
                    Save
                  </button>
                </div>
                <p className="text-xs text-yellow-600 mt-1">Your API key is stored locally and only used for your questions about TC.</p>
              </div>
            )}

            {/* Question counter and API key status */}
            {!userApiKey && questionsUsed < 5 && messages.length > 0 && (
              <div className="mb-2 text-center">
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                  Free questions: {questionsUsed}/5 used
                </span>
              </div>
            )}
            
            {/* API key status with clear option */}
            {userApiKey && (
              <div className="mb-2 text-center">
                <div className="flex items-center justify-center gap-2 text-xs">
                  <span className="text-green-600 bg-green-100 px-2 py-1 rounded-full">
                    ✅ Using your API key
                  </span>
                  <button
                    onClick={() => {
                      setUserApiKey("");
                      setShowApiKeyInput(false);
                    }}
                    className="text-red-600 bg-red-100 px-2 py-1 rounded-full hover:bg-red-200 transition-colors"
                    title="Clear API key and end session"
                  >
                    🗑️ Clear
                  </button>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                onClick={() => {
                  if (questionsUsed >= 5 && !userApiKey) {
                    setShowApiKeyInput(true);
                  }
                }}
                placeholder={questionsUsed >= 5 && !userApiKey ? "Add API key to continue..." : "Ask about my experience, skills, projects..."}
                disabled={questionsUsed >= 5 && !userApiKey}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring focus:ring-blue-300 disabled:bg-gray-100 disabled:cursor-pointer"
              />
              <button
                onClick={() => {
                  if (questionsUsed >= 5 && !userApiKey) {
                    setShowApiKeyInput(true);
                  } else {
                    sendMessage();
                  }
                }}
                className="bg-yellow-600 text-white px-4 py-2 text-sm rounded-lg hover:bg-yellow-500 focus:outline-none disabled:bg-gray-400 disabled:cursor-pointer"
                disabled={false}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatbotUI;
