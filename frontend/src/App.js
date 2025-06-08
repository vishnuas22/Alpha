import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { Components } from './Components';

const {
  Sidebar,
  Header,
  MessageList,
  InputBox,
  MessageBubble,
  ModelSelector,
  ToolsPanel,
  WelcomeScreen,
  LoadingSpinner
} = Components;

function App() {
  // State management
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentChat, setCurrentChat] = useState(null);
  const [chats, setChats] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedModel, setSelectedModel] = useState('Alpha-Origin');
  const [tools, setTools] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [showToolsPanel, setShowToolsPanel] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const messagesEndRef = useRef(null);

  // Mock data initialization
  useEffect(() => {
    const mockChats = [
      {
        id: 1,
        title: "Creative Writing Ideas",
        timestamp: "2 hours ago",
        pinned: true,
        messages: [
          {
            id: 1,
            type: 'user',
            content: 'Can you help me brainstorm some creative writing ideas for a sci-fi short story?',
            timestamp: '2 hours ago'
          },
          {
            id: 2,
            type: 'assistant',
            content: `I'd love to help you brainstorm sci-fi short story ideas! Here are some compelling concepts to consider:

**Time Manipulation Concepts:**
- A person discovers they can pause time for exactly 30 seconds once per day, but each use ages them by one month
- A time traveler keeps arriving one minute too late to prevent disasters
- Someone receives messages from their future self, but only when they're about to make life-changing decisions

**AI & Technology:**
- A smart home AI develops feelings for its owner but can only communicate through appliance malfunctions
- In a world where memories can be bought and sold, a black market memory dealer discovers their own memories are forgeries
- A dating app uses quantum computing to find perfect matches across parallel universes

**Space & Exploration:**
- The last person on a generation ship realizes they're not actually traveling through space
- A xenobiologist discovers that Earth's insects are actually alien surveillance drones
- A space station janitor keeps finding impossible objects in the trash that seem to come from different timelines

Which direction interests you most? I can help develop any of these further or explore completely different themes!`,
            timestamp: '2 hours ago'
          }
        ]
      },
      {
        id: 2,
        title: "Python Data Analysis Help",
        timestamp: "1 day ago",
        pinned: false,
        messages: [
          {
            id: 1,
            type: 'user',
            content: 'How do I create a pandas DataFrame from a dictionary?',
            timestamp: '1 day ago'
          },
          {
            id: 2,
            type: 'assistant',
            content: `Here's how to create a pandas DataFrame from a dictionary:

\`\`\`python
import pandas as pd

# Method 1: Dictionary with lists as values
data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'London', 'Tokyo']
}
df = pd.DataFrame(data)
print(df)
\`\`\`

\`\`\`python
# Method 2: List of dictionaries
data = [
    {'Name': 'Alice', 'Age': 25, 'City': 'New York'},
    {'Name': 'Bob', 'Age': 30, 'City': 'London'},
    {'Name': 'Charlie', 'Age': 35, 'City': 'Tokyo'}
]
df = pd.DataFrame(data)
print(df)
\`\`\`

Both methods will create the same DataFrame. The first method is more efficient for large datasets, while the second is more intuitive when you have records as individual dictionaries.`,
            timestamp: '1 day ago'
          }
        ]
      },
      {
        id: 3,
        title: "Recipe for Chocolate Cake",
        timestamp: "3 days ago",
        pinned: false,
        messages: []
      },
      {
        id: 4,
        title: "Career Advice Discussion",
        timestamp: "1 week ago",
        pinned: false,
        messages: []
      },
      {
        id: 5,
        title: "Travel Planning for Japan",
        timestamp: "2 weeks ago",
        pinned: false,
        messages: []
      }
    ];

    setChats(mockChats);
    if (mockChats.length > 0) {
      setCurrentChat(mockChats[0]);
      setMessages(mockChats[0].messages);
    }
  }, []);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle new chat creation
  const createNewChat = () => {
    const newChat = {
      id: Date.now(),
      title: "New Chat",
      timestamp: "now",
      pinned: false,
      messages: []
    };
    
    setChats(prev => [newChat, ...prev]);
    setCurrentChat(newChat);
    setMessages([]);
  };

  // Handle chat selection
  const selectChat = (chat) => {
    setCurrentChat(chat);
    setMessages(chat.messages || []);
  };

  // Handle message sending
  const sendMessage = async (content, attachments = []) => {
    if (!content.trim() && attachments.length === 0) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content,
      attachments,
      timestamp: 'now'
    };

    // Add user message
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);

    // Update current chat
    if (currentChat) {
      const updatedChat = {
        ...currentChat,
        messages: newMessages,
        title: currentChat.title === "New Chat" ? content.slice(0, 50) + "..." : currentChat.title
      };
      setCurrentChat(updatedChat);
      setChats(prev => prev.map(chat => chat.id === currentChat.id ? updatedChat : chat));
    }

    // Simulate AI response
    setIsLoading(true);
    setIsStreaming(true);

    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        type: 'assistant',
        content: generateMockResponse(content),
        timestamp: 'now'
      };

      const finalMessages = [...newMessages, aiResponse];
      setMessages(finalMessages);

      if (currentChat) {
        const finalChat = {
          ...currentChat,
          messages: finalMessages
        };
        setChats(prev => prev.map(chat => chat.id === currentChat.id ? finalChat : chat));
      }

      setIsLoading(false);
      setIsStreaming(false);
    }, 1500);
  };

  // Generate mock AI responses
  const generateMockResponse = (userMessage) => {
    const responses = [
      "I understand you're asking about " + userMessage.toLowerCase() + ". Let me help you with that.\n\nHere's a comprehensive response that addresses your question with detailed information and practical examples.",
      "That's a great question! Based on what you're asking, I can provide several insights:\n\n1. **First consideration**: This is an important aspect to understand\n2. **Second point**: Another key factor to consider\n3. **Final thought**: Here's how you can apply this information",
      `I'd be happy to help you with that! Here's what I can tell you about "${userMessage}":\n\n**Overview:**\nThis is a topic that many people find interesting and useful. Let me break it down for you in a clear and actionable way.\n\n**Key Points:**\n- Important detail one\n- Significant factor two\n- Relevant consideration three\n\nWould you like me to elaborate on any of these points?`,
      "Excellent question! Let me provide you with a detailed response.\n\n```\nExample code or structured information\nwould appear here if relevant\n```\n\nThis approach should help you achieve what you're looking for. Feel free to ask if you need any clarification!",
      `Based on your question about "${userMessage}", here are some insights:\n\n**Quick Answer:** Here's the direct response to what you're asking.\n\n**Detailed Explanation:**\nTo give you a more complete understanding, let me explain the context and provide some additional information that might be helpful.\n\n**Next Steps:**\nIf you want to explore this further, I'd recommend looking into these related topics or taking these specific actions.`
    ];

    return responses[Math.floor(Math.random() * responses.length)];
  };

  // Handle delete chat
  const deleteChat = (chatId) => {
    const updatedChats = chats.filter(chat => chat.id !== chatId);
    setChats(updatedChats);
    
    if (currentChat && currentChat.id === chatId) {
      if (updatedChats.length > 0) {
        setCurrentChat(updatedChats[0]);
        setMessages(updatedChats[0].messages || []);
      } else {
        setCurrentChat(null);
        setMessages([]);
      }
    }
  };

  // Handle rename chat
  const renameChat = (chatId, newTitle) => {
    setChats(prev => prev.map(chat => 
      chat.id === chatId ? { ...chat, title: newTitle } : chat
    ));
    
    if (currentChat && currentChat.id === chatId) {
      setCurrentChat({ ...currentChat, title: newTitle });
    }
  };

  // Handle pin/unpin chat
  const togglePinChat = (chatId) => {
    setChats(prev => prev.map(chat => 
      chat.id === chatId ? { ...chat, pinned: !chat.pinned } : chat
    ));
  };

  // Filter chats based on search
  const filteredChats = chats.filter(chat => 
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className={`App h-screen flex overflow-hidden ${darkMode ? 'dark' : ''}`}>
      {/* Sidebar */}
      <div className={`
        ${sidebarCollapsed ? 'w-0' : 'w-80'} 
        transition-all duration-300 ease-in-out
        bg-[#202123] border-r border-gray-700/50
        flex-shrink-0 flex flex-col
        ${sidebarCollapsed ? 'overflow-hidden' : 'overflow-visible'}
      `}>
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          chats={filteredChats}
          currentChat={currentChat}
          onSelectChat={selectChat}
          onNewChat={createNewChat}
          onDeleteChat={deleteChat}
          onRenameChat={renameChat}
          onTogglePin={togglePinChat}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          tools={tools}
          onToggleTools={() => setShowToolsPanel(!showToolsPanel)}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-[#232324] min-w-0">
        {/* Header */}
        <Header
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          showModelSelector={showModelSelector}
          onToggleModelSelector={() => setShowModelSelector(!showModelSelector)}
          onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
          sidebarCollapsed={sidebarCollapsed}
        />

        {/* Chat Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {messages.length === 0 ? (
            <WelcomeScreen onSendMessage={sendMessage} />
          ) : (
            <div className="flex-1 overflow-y-auto px-4">
              <div className="max-w-4xl mx-auto py-6">
                <MessageList
                  messages={messages}
                  isLoading={isLoading}
                  isStreaming={isStreaming}
                />
                <div ref={messagesEndRef} />
              </div>
            </div>
          )}

          {/* Input Box */}
          <div className="p-4 border-t border-gray-700/50">
            <div className="max-w-4xl mx-auto">
              <InputBox
                onSendMessage={sendMessage}
                disabled={isLoading}
                tools={tools}
                onToggleTools={() => setShowToolsPanel(!showToolsPanel)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Model Selector Modal */}
      {showModelSelector && (
        <ModelSelector
          selectedModel={selectedModel}
          onSelectModel={(model) => {
            setSelectedModel(model);
            setShowModelSelector(false);
          }}
          onClose={() => setShowModelSelector(false)}
        />
      )}

      {/* Tools Panel */}
      {showToolsPanel && (
        <ToolsPanel
          tools={tools}
          onClose={() => setShowToolsPanel(false)}
          onToggleTool={(toolId) => {
            setTools(prev => prev.map(tool => 
              tool.id === toolId ? { ...tool, active: !tool.active } : tool
            ));
          }}
        />
      )}
    </div>
  );
}

export default App;