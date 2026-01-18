import React, { useState, useEffect } from 'react';
import { FREE_QUESTIONS_LIMIT, FREE_QUESTIONS_WARNING_THRESHOLD } from '../config/chatbot';

type Message = { sender: "user" | "bot"; text: string };

const ChatbotUI = () => {
  const [isOpen, setIsOpen] = useState(false); // Toggle chatbot open/close
  const [messages, setMessages] = useState<Message[]>([]); // Chat messages
  const [input, setInput] = useState(""); // User input
  const [isExpanded, setIsExpanded] = useState(false); // Track if chatbot should be expanded
  const [questionsUsed, setQuestionsUsed] = useState(0); // Track free questions used
  const [userApiKey, setUserApiKey] = useState(""); // User's own API key
  const [showApiKeyInput, setShowApiKeyInput] = useState(false); // Show API key input

  // Inject scrollbar styles optimized for iOS and all platforms
  useEffect(() => {
    const style = document.createElement('style');
    style.innerHTML = `
      .chatbot-body {
        flex: 1 1 auto;
        overflow-y: auto;
        overflow-x: hidden;
        -webkit-overflow-scrolling: touch;
        overscroll-behavior: contain;
        touch-action: pan-y;
        scrollbar-width: thin;
        scrollbar-color: #d97706 #f3f4f6;
      }

      .chatbot-body::-webkit-scrollbar {
        width: 8px;
      }

      .chatbot-body::-webkit-scrollbar-thumb {
        background: #d97706;
        border-radius: 4px;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  // Prevent body scroll when chatbot is expanded or open on mobile (iOS fix)
  useEffect(() => {
    const isMobile = window.innerWidth < 768;

    if (isExpanded || (isOpen && isMobile)) {
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed'; // iOS fix
      document.body.style.width = '100%';     // Prevent width change
    } else {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    }

    // Cleanup on unmount
    return () => {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    };
  }, [isExpanded, isOpen]);

  // Handle iOS viewport height changes due to keyboard
  useEffect(() => {
    const handleResize = () => {
      // Update CSS custom property for real viewport height
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
    if (questionsUsed >= FREE_QUESTIONS_LIMIT && !userApiKey) {
      setShowApiKeyInput(true);
      setMessages((prev) => [...prev,
        { sender: "user", text: input.trim() },
        { sender: "bot", text: `You've used your ${FREE_QUESTIONS_LIMIT} free questions! To continue asking about my experience and projects, use your OpenAI API key below.` }
      ]);
      setInput("");
      return;
    }

    const apiUrl = import.meta.env.PUBLIC_CHATBOT_API_URL;
    const userMessage = input.trim();

    // Expand chatbot on first message (only on desktop)
    if (messages.length === 0 && window.innerWidth >= 768) {
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
      if (!userApiKey && questionsUsed === FREE_QUESTIONS_WARNING_THRESHOLD) {
        const questionsLeft = FREE_QUESTIONS_LIMIT - questionsUsed;
        setMessages((prev) => [...prev, {
          sender: "bot",
          text: `⚠️ You have ${questionsLeft} free ${questionsLeft === 1 ? 'question' : 'questions'} remaining. After that, use your OpenAI API key to continue.`
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
      {/* Blur backdrop when expanded - click to minimize */}
      {isOpen && isExpanded && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-40 cursor-pointer"
          onClick={() => setIsExpanded(false)}
          title="Click to minimize chatbot"
        />
      )}

      {/* Semi-transparent backdrop when open (but not expanded) on mobile */}
      {isOpen && !isExpanded && (
        <div
          className="fixed inset-0 bg-transparent z-30 md:hidden"
          onClick={(e) => {
            // Only close if clicking outside the chatbot
            if (e.target === e.currentTarget) {
              setIsOpen(false);
            }
          }}
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
            ? 'inset-4 md:inset-y-12 md:right-6 md:left-auto md:w-[550px]'
            : 'bottom-4 left-4 right-4 h-[90vh] md:h-auto md:max-h-[70vh] md:bottom-20 md:left-auto md:right-4 md:w-[460px]'
        }`}>
          <div className="bg-yellow-600 text-white p-2 md:p-3 flex justify-between items-center rounded-t-lg flex-shrink-0">
            <h3 className="font-bold text-xs sm:text-sm truncate pr-2">TC Heiner - Ask me anything!</h3>
            <div className="flex gap-1 md:gap-2 flex-shrink-0">
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
          <div className="flex-1 overflow-hidden">
            <div className="chatbot-body h-full p-2 md:p-3">
              {messages.length === 0 ? (
                <div className="text-gray-600 text-sm text-center space-y-2 md:space-y-3">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="font-semibold text-blue-800 mb-2 text-sm">👋 Hi! I'm TC Heiner's chatbot, here to answer questions about my work and projects.</p>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="font-semibold text-green-800 mb-1 text-sm">🎁 Free Questions</p>
                    <p className="text-green-700 text-sm">You get <strong>{FREE_QUESTIONS_LIMIT} free questions</strong> about TC's work.</p>
                    <p className="text-green-600 text-xs mt-1">After that, use your OpenAI API key to continue.</p>
                  </div>
                  <p className="text-gray-500 text-xs">Questions remaining: <strong>{FREE_QUESTIONS_LIMIT - questionsUsed}</strong></p>
                </div>
              ) : (
                <>
                  {messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`mb-3 ${msg.sender === "user" ? "text-right" : "text-left"}`}
                    >
                      <span
                        className={`inline-block px-3 py-2 rounded-lg text-sm leading-relaxed max-w-[85%] ${
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
                </>
              )}
            </div>
          </div>
          <div className="border-t border-gray-200 flex-shrink-0 p-2 md:p-3">
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
            {!userApiKey && questionsUsed < FREE_QUESTIONS_LIMIT && messages.length > 0 && (
              <div className="mb-2 text-center">
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                  Free questions: {questionsUsed}/{FREE_QUESTIONS_LIMIT} used
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

            <div className="flex items-center gap-2 w-full">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                onClick={() => {
                  if (questionsUsed >= FREE_QUESTIONS_LIMIT && !userApiKey) {
                    setShowApiKeyInput(true);
                  }
                }}
                placeholder={questionsUsed >= FREE_QUESTIONS_LIMIT && !userApiKey ? "Add API key..." : "Ask about my experience..."}
                disabled={questionsUsed >= FREE_QUESTIONS_LIMIT && !userApiKey}
                className="flex-1 min-w-0 px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring focus:ring-blue-300 disabled:bg-gray-100 disabled:cursor-pointer"
              />
              <button
                onClick={() => {
                  if (questionsUsed >= FREE_QUESTIONS_LIMIT && !userApiKey) {
                    setShowApiKeyInput(true);
                  } else {
                    sendMessage();
                  }
                }}
                className="bg-yellow-600 text-white px-4 py-2.5 text-sm rounded-lg hover:bg-yellow-500 focus:outline-none flex-shrink-0 whitespace-nowrap"
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
