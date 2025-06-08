import React, { useState, useRef, useEffect } from 'react';

// Icons as SVG components
const Icons = {
  Plus: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="5" x2="12" y2="19"></line>
      <line x1="5" y1="12" x2="19" y2="12"></line>
    </svg>
  ),
  Search: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8"></circle>
      <path d="m21 21-4.35-4.35"></path>
    </svg>
  ),
  Menu: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="3" y1="6" x2="21" y2="6"></line>
      <line x1="3" y1="12" x2="21" y2="12"></line>
      <line x1="3" y1="18" x2="21" y2="18"></line>
    </svg>
  ),
  ChevronDown: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="6,9 12,15 18,9"></polyline>
    </svg>
  ),
  Send: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="22" y1="2" x2="11" y2="13"></line>
      <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
    </svg>
  ),
  Mic: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
      <line x1="12" y1="19" x2="12" y2="23"></line>
      <line x1="8" y1="23" x2="16" y2="23"></line>
    </svg>
  ),
  Copy: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
  ),
  ThumbsUp: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
    </svg>
  ),
  ThumbsDown: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
    </svg>
  ),
  MoreVertical: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="1"></circle>
      <circle cx="12" cy="5" r="1"></circle>
      <circle cx="12" cy="19" r="1"></circle>
    </svg>
  ),
  Pin: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 17l1-1v-6l-2-2-2 2v6l1 1"></path>
      <path d="M8 21l4-7 4 7"></path>
    </svg>
  ),
  Edit: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
    </svg>
  ),
  Trash: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="3,6 5,6 21,6"></polyline>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
    </svg>
  ),
  User: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
      <circle cx="12" cy="7" r="4"></circle>
    </svg>
  ),
  Settings: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="3"></circle>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    </svg>
  ),
  Refresh: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23,4 23,10 17,10"></polyline>
      <polyline points="1,20 1,14 7,14"></polyline>
      <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
    </svg>
  ),
  Attachment: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66L9.64 16.2a2 2 0 0 1-2.83-2.83l8.49-8.49"></path>
    </svg>
  ),
  X: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="6" x2="6" y2="18"></line>
      <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
  ),
  AlphaLogo: () => (
    <div className="w-8 h-8 bg-gradient-to-br from-[#10a37f] to-[#0d8268] rounded-lg flex items-center justify-center text-white font-bold text-sm">
      A
    </div>
  )
};

// Sidebar Component
const Sidebar = ({ 
  collapsed, 
  onToggleCollapse, 
  chats, 
  currentChat, 
  onSelectChat, 
  onNewChat,
  onDeleteChat,
  onRenameChat,
  onTogglePin,
  searchQuery,
  onSearchChange,
  tools,
  onToggleTools
}) => {
  const [contextMenu, setContextMenu] = useState({ show: false, x: 0, y: 0, chatId: null });
  const [editingChat, setEditingChat] = useState(null);

  const handleRightClick = (e, chatId) => {
    e.preventDefault();
    setContextMenu({
      show: true,
      x: e.clientX,
      y: e.clientY,
      chatId
    });
  };

  const handleContextAction = (action) => {
    const { chatId } = contextMenu;
    setContextMenu({ show: false, x: 0, y: 0, chatId: null });

    switch (action) {
      case 'rename':
        setEditingChat(chatId);
        break;
      case 'pin':
        onTogglePin(chatId);
        break;
      case 'delete':
        onDeleteChat(chatId);
        break;
    }
  };

  const handleRename = (chatId, newTitle) => {
    onRenameChat(chatId, newTitle);
    setEditingChat(null);
  };

  useEffect(() => {
    const handleClickOutside = () => {
      setContextMenu({ show: false, x: 0, y: 0, chatId: null });
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  if (collapsed) return null;

  return (
    <>
      <div className="h-full flex flex-col p-3">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Icons.AlphaLogo />
            <span className="text-white font-semibold text-lg">Alpha</span>
          </div>
          <button
            onClick={onToggleCollapse}
            className="p-1 text-gray-400 hover:text-white transition-colors lg:hidden"
          >
            <Icons.X />
          </button>
        </div>

        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="w-full flex items-center space-x-3 px-4 py-3 bg-[#10a37f] hover:bg-[#0d8268] text-white rounded-lg transition-colors duration-200 mb-4"
        >
          <Icons.Plus />
          <span>New chat</span>
        </button>

        {/* Search */}
        <div className="relative mb-4">
          <Icons.Search />
          <input
            type="text"
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#40414f] text-white rounded-lg border border-gray-600 focus:border-[#10a37f] focus:outline-none transition-colors"
          />
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
            <Icons.Search />
          </div>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto space-y-1">
          {chats.length === 0 ? (
            <div className="text-gray-400 text-center py-8">
              No chats yet. Start a new conversation!
            </div>
          ) : (
            chats.map((chat) => (
              <ChatItem
                key={chat.id}
                chat={chat}
                isActive={currentChat?.id === chat.id}
                onClick={() => onSelectChat(chat)}
                onRightClick={(e) => handleRightClick(e, chat.id)}
                isEditing={editingChat === chat.id}
                onRename={(newTitle) => handleRename(chat.id, newTitle)}
                onCancelEdit={() => setEditingChat(null)}
              />
            ))
          )}
        </div>

        {/* Tools Section */}
        <div className="border-t border-gray-600 pt-4 mt-4">
          <div className="text-gray-400 text-sm mb-2">Tools</div>
          <button
            onClick={onToggleTools}
            className="w-full text-left px-3 py-2 text-gray-300 hover:bg-[#40414f] rounded-lg transition-colors"
          >
            Manage tools
          </button>
        </div>

        {/* User Section */}
        <div className="border-t border-gray-600 pt-4 mt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 px-3 py-2">
              <div className="w-8 h-8 bg-[#10a37f] rounded-full flex items-center justify-center">
                <Icons.User />
              </div>
              <span className="text-gray-300">User</span>
            </div>
            <button className="p-2 text-gray-400 hover:text-white transition-colors">
              <Icons.Settings />
            </button>
          </div>
        </div>
      </div>

      {/* Context Menu */}
      {contextMenu.show && (
        <div
          className="fixed bg-[#40414f] border border-gray-600 rounded-lg shadow-lg py-2 z-50"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          <button
            onClick={() => handleContextAction('rename')}
            className="w-full text-left px-4 py-2 hover:bg-[#525362] text-white flex items-center space-x-2"
          >
            <Icons.Edit />
            <span>Rename</span>
          </button>
          <button
            onClick={() => handleContextAction('pin')}
            className="w-full text-left px-4 py-2 hover:bg-[#525362] text-white flex items-center space-x-2"
          >
            <Icons.Pin />
            <span>Pin</span>
          </button>
          <button
            onClick={() => handleContextAction('delete')}
            className="w-full text-left px-4 py-2 hover:bg-[#525362] text-red-400 flex items-center space-x-2"
          >
            <Icons.Trash />
            <span>Delete</span>
          </button>
        </div>
      )}
    </>
  );
};

// Chat Item Component
const ChatItem = ({ 
  chat, 
  isActive, 
  onClick, 
  onRightClick, 
  isEditing, 
  onRename, 
  onCancelEdit 
}) => {
  const [editValue, setEditValue] = useState(chat.title);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editValue.trim()) {
      onRename(editValue.trim());
    } else {
      onCancelEdit();
    }
  };

  if (isEditing) {
    return (
      <form onSubmit={handleSubmit} className="px-3 py-2">
        <input
          ref={inputRef}
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={handleSubmit}
          className="w-full bg-[#40414f] text-white border border-gray-600 rounded px-2 py-1 text-sm"
        />
      </form>
    );
  }

  return (
    <div
      onClick={onClick}
      onContextMenu={onRightClick}
      className={`
        px-3 py-2 rounded-lg cursor-pointer transition-colors duration-200 group
        ${isActive 
          ? 'bg-[#40414f] border-l-2 border-[#10a37f]' 
          : 'hover:bg-[#2a2b32]'
        }
      `}
    >
      <div className="flex items-center space-x-3">
        {chat.pinned && (
          <div className="text-[#10a37f]">
            <Icons.Pin />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="text-white text-sm font-medium truncate">
            {chat.title}
          </div>
          <div className="text-gray-400 text-xs">
            {chat.timestamp}
          </div>
        </div>
        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
          <Icons.MoreVertical />
        </div>
      </div>
    </div>
  );
};

// Header Component
const Header = ({ 
  selectedModel, 
  onModelChange, 
  showModelSelector, 
  onToggleModelSelector,
  onToggleSidebar,
  sidebarCollapsed
}) => {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700/50">
      <div className="flex items-center space-x-4">
        {sidebarCollapsed && (
          <button
            onClick={onToggleSidebar}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <Icons.Menu />
          </button>
        )}
        
        <button
          onClick={onToggleModelSelector}
          className="flex items-center space-x-2 px-3 py-2 bg-[#40414f] hover:bg-[#525362] text-white rounded-lg transition-colors"
        >
          <span className="font-medium">{selectedModel}</span>
          <Icons.ChevronDown />
        </button>
      </div>

      <div className="flex items-center space-x-3">
        <button className="p-2 text-gray-400 hover:text-white transition-colors">
          <Icons.Refresh />
        </button>
        <button className="p-2 text-gray-400 hover:text-white transition-colors">
          <Icons.User />
        </button>
      </div>
    </div>
  );
};

// Welcome Screen Component
const WelcomeScreen = ({ onSendMessage }) => {
  const suggestions = [
    "Explain quantum computing like I'm 5",
    "Write a creative story about time travel",
    "Help me plan a healthy meal prep for the week",
    "What are the latest trends in web development?"
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-8">
      <div className="max-w-2xl mx-auto text-center">
        {/* Logo */}
        <div className="mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-[#10a37f] to-[#0d8268] rounded-2xl flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4">
            A
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">
            How can I help you today?
          </h1>
          <p className="text-gray-400">
            Start a conversation with Alpha and explore the possibilities
          </p>
        </div>

        {/* Suggestions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-8">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => onSendMessage(suggestion)}
              className="p-4 bg-[#40414f] hover:bg-[#525362] text-left text-white rounded-lg transition-colors border border-gray-600 hover:border-gray-500"
            >
              <div className="text-sm">{suggestion}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// Message List Component
const MessageList = ({ messages, isLoading, isStreaming }) => {
  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      
      {isLoading && (
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-[#10a37f] to-[#0d8268] rounded-full flex items-center justify-center text-white font-bold text-sm">
            A
          </div>
          <div className="flex-1">
            <LoadingSpinner />
          </div>
        </div>
      )}
    </div>
  );
};

// Message Bubble Component
const MessageBubble = ({ message }) => {
  const [showActions, setShowActions] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isUser = message.type === 'user';

  return (
    <div 
      className="group"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex items-start space-x-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {isUser ? (
            <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
              <Icons.User />
            </div>
          ) : (
            <div className="w-8 h-8 bg-gradient-to-br from-[#10a37f] to-[#0d8268] rounded-full flex items-center justify-center text-white font-bold text-sm">
              A
            </div>
          )}
        </div>

        {/* Message Content */}
        <div className="flex-1 min-w-0">
          <div className="text-white leading-relaxed">
            <MessageContent content={message.content} />
          </div>
          
          {/* Message Actions */}
          <div className={`
            flex items-center space-x-2 mt-2 transition-opacity duration-200
            ${showActions ? 'opacity-100' : 'opacity-0'}
          `}>
            <button
              onClick={handleCopy}
              className="p-1 text-gray-400 hover:text-white transition-colors"
              title={copied ? 'Copied!' : 'Copy'}
            >
              <Icons.Copy />
            </button>
            {!isUser && (
              <>
                <button className="p-1 text-gray-400 hover:text-white transition-colors" title="Good response">
                  <Icons.ThumbsUp />
                </button>
                <button className="p-1 text-gray-400 hover:text-white transition-colors" title="Bad response">
                  <Icons.ThumbsDown />
                </button>
                <button className="p-1 text-gray-400 hover:text-white transition-colors" title="Regenerate">
                  <Icons.Refresh />
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Message Content Component (handles markdown-like formatting)
const MessageContent = ({ content }) => {
  // Simple markdown-like parsing
  const parseContent = (text) => {
    // Split by code blocks
    const parts = text.split(/(```[\s\S]*?```)/);
    
    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        // Code block
        const code = part.slice(3, -3).trim();
        const lines = code.split('\n');
        const language = lines[0];
        const codeContent = lines.slice(1).join('\n');
        
        return (
          <CodeBlock key={index} language={language} code={codeContent} />
        );
      } else {
        // Regular text with inline formatting
        return (
          <div key={index} className="whitespace-pre-wrap">
            {formatInlineText(part)}
          </div>
        );
      }
    });
  };

  const formatInlineText = (text) => {
    // Simple bold formatting **text**
    return text.split(/(\*\*.*?\*\*)/).map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return <div>{parseContent(content)}</div>;
};

// Code Block Component
const CodeBlock = ({ language, code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-[#1e1e1e] rounded-lg my-4 overflow-hidden border border-gray-700">
      <div className="flex items-center justify-between px-4 py-2 bg-[#2d2d2d] border-b border-gray-700">
        <span className="text-gray-400 text-sm">{language}</span>
        <button
          onClick={handleCopy}
          className="text-gray-400 hover:text-white transition-colors text-sm flex items-center space-x-1"
        >
          <Icons.Copy />
          <span>{copied ? 'Copied!' : 'Copy'}</span>
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm">
        <code className="text-gray-100">{code}</code>
      </pre>
    </div>
  );
};

// Input Box Component
const InputBox = ({ onSendMessage, disabled, tools, onToggleTools }) => {
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState([]);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() && attachments.length === 0) return;

    onSendMessage(input, attachments);
    setInput('');
    setAttachments([]);
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
    
    // Auto-resize textarea
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const canSend = input.trim() || attachments.length > 0;

  return (
    <div className="w-full">
      {/* Attachments */}
      {attachments.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {attachments.map((file, index) => (
            <div key={index} className="flex items-center space-x-2 bg-[#40414f] px-3 py-1 rounded-lg">
              <span className="text-sm text-gray-300">{file.name}</span>
              <button
                onClick={() => removeAttachment(index)}
                className="text-gray-400 hover:text-white"
              >
                <Icons.X />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Container */}
      <div className="relative bg-[#343541] rounded-xl border border-gray-600 focus-within:border-[#10a37f] transition-colors">
        <div className="flex items-end space-x-3 p-3">
          {/* Attachment Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex-shrink-0 p-2 text-gray-400 hover:text-white transition-colors"
            disabled={disabled}
          >
            <Icons.Plus />
          </button>

          {/* Text Input */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Message Alpha..."
            disabled={disabled}
            className="flex-1 bg-transparent text-white placeholder-gray-400 resize-none outline-none min-h-[24px] max-h-32"
            rows="1"
          />

          {/* Voice Button */}
          <button
            className="flex-shrink-0 p-2 text-gray-400 hover:text-white transition-colors"
            disabled={disabled}
          >
            <Icons.Mic />
          </button>

          {/* Send Button */}
          <button
            onClick={handleSubmit}
            disabled={disabled || !canSend}
            className={`
              flex-shrink-0 p-2 rounded-lg transition-colors
              ${canSend && !disabled
                ? 'bg-[#10a37f] hover:bg-[#0d8268] text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            <Icons.Send />
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="text-center text-xs text-gray-500 mt-2">
        Alpha can make mistakes. Check important info.
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        accept="image/*,.pdf,.doc,.docx,.txt"
      />
    </div>
  );
};

// Model Selector Component
const ModelSelector = ({ selectedModel, onSelectModel, onClose }) => {
  const models = [
    {
      id: 'alpha-origin',
      name: 'Alpha-Origin',
      description: 'Fastest model for everyday tasks',
      badge: 'Faster'
    },
    {
      id: 'alpha-prime',
      name: 'Alpha-Prime', 
      description: 'Most capable model for complex reasoning',
      badge: 'Smarter'
    }
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[#40414f] rounded-lg shadow-xl p-6 w-96 max-w-[90vw]" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white text-lg font-semibold">Select Model</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <Icons.X />
          </button>
        </div>

        <div className="space-y-3">
          {models.map((model) => (
            <button
              key={model.id}
              onClick={() => onSelectModel(model.name)}
              className={`
                w-full text-left p-4 rounded-lg border transition-colors
                ${selectedModel === model.name
                  ? 'border-[#10a37f] bg-[#10a37f]/10'
                  : 'border-gray-600 hover:border-gray-500 hover:bg-[#525362]'
                }
              `}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-white font-medium">{model.name}</span>
                <span className="text-xs bg-[#10a37f] text-white px-2 py-1 rounded">
                  {model.badge}
                </span>
              </div>
              <div className="text-gray-400 text-sm">{model.description}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// Tools Panel Component
const ToolsPanel = ({ tools, onClose, onToggleTool }) => {
  const availableTools = [
    { id: 1, name: 'Web Search', description: 'Search the web for current information', icon: '🔍' },
    { id: 2, name: 'Code Interpreter', description: 'Run Python code and analyze data', icon: '💻' },
    { id: 3, name: 'Image Generator', description: 'Create images from text descriptions', icon: '🎨' },
    { id: 4, name: 'Document Reader', description: 'Read and analyze PDF documents', icon: '📄' }
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[#40414f] rounded-lg shadow-xl p-6 w-96 max-w-[90vw]" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white text-lg font-semibold">Tools</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <Icons.X />
          </button>
        </div>

        <div className="space-y-3">
          {availableTools.map((tool) => (
            <div key={tool.id} className="flex items-center justify-between p-3 border border-gray-600 rounded-lg">
              <div className="flex items-center space-x-3">
                <span className="text-xl">{tool.icon}</span>
                <div>
                  <div className="text-white font-medium">{tool.name}</div>
                  <div className="text-gray-400 text-sm">{tool.description}</div>
                </div>
              </div>
              <button
                onClick={() => onToggleTool(tool.id)}
                className={`
                  w-10 h-6 rounded-full transition-colors relative
                  ${tools.find(t => t.id === tool.id)?.active 
                    ? 'bg-[#10a37f]' 
                    : 'bg-gray-600'
                  }
                `}
              >
                <div className={`
                  w-4 h-4 bg-white rounded-full absolute top-1 transition-transform
                  ${tools.find(t => t.id === tool.id)?.active 
                    ? 'translate-x-5' 
                    : 'translate-x-1'
                  }
                `} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Loading Spinner Component
const LoadingSpinner = () => {
  return (
    <div className="flex items-center space-x-2 text-gray-400">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{animationDelay: '0.1s'}}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
      </div>
      <span className="text-sm">Alpha is thinking...</span>
    </div>
  );
};

export const Components = {
  Sidebar,
  Header,
  MessageList,
  InputBox,
  MessageBubble,
  ModelSelector,
  ToolsPanel,
  WelcomeScreen,
  LoadingSpinner,
  Icons
};