import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import ReactMarkdown from 'react-markdown';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [sessionId, setSessionId] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [popularSuggestions, setPopularSuggestions] = useState([]);
  const recognitionRef = useRef(null);

  // Initialize session
  useEffect(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    loadPopularSuggestions();
    initVoiceRecognition();
  }, []);

  const loadPopularSuggestions = async () => {
    try {
      const response = await axios.get(`${API}/search/suggestions`);
      setPopularSuggestions(response.data.suggestions);
    } catch (error) {
      console.error("Error loading suggestions:", error);
    }
  };

  const initVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  };

  const startVoiceInput = () => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const handleSearch = async (searchQuery = query) => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    try {
      const searchResponse = await axios.post(`${API}/search`, {
        query: searchQuery,
        session_id: sessionId
      });

      setResponse(searchResponse.data.response);
      setSuggestions(searchResponse.data.suggestions);
      
      // Add to history
      const newHistory = {
        query: searchQuery,
        response: searchResponse.data.response,
        timestamp: new Date().toISOString()
      };
      setSearchHistory(prev => [newHistory, ...prev.slice(0, 4)]);

    } catch (error) {
      console.error("Search error:", error);
      setResponse("I apologize, but I'm experiencing technical difficulties. Please try again in a moment.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    handleSearch(suggestion);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">α</div>
            <span className="logo-text">Alpha</span>
          </div>
          <button className="upgrade-btn">
            <span className="upgrade-icon">⚡</span>
            Upgrade
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {!response ? (
          // Welcome Screen
          <div className="welcome-screen">
            <div className="welcome-icon">
              <div className="planet-icon">🌍</div>
            </div>
            <h1 className="welcome-title">Good to See You!</h1>
            <h2 className="welcome-subtitle">How Can I be an Assistance?</h2>
            <p className="welcome-description">I'm available 24/7 for you, ask me anything</p>

            {/* Search Bar */}
            <div className="search-container">
              <div className="search-bar">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask anything..."
                  className="search-input"
                  disabled={isLoading}
                />
                <button 
                  onClick={startVoiceInput}
                  className={`voice-btn ${isListening ? 'listening' : ''}`}
                  disabled={isLoading}
                >
                  🎤
                </button>
              </div>
              {isLoading && <div className="loading-indicator">⚡ Searching...</div>}
            </div>

            {/* Popular Suggestions */}
            <div className="suggestions-grid">
              {popularSuggestions.slice(0, 4).map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="suggestion-card"
                >
                  <span className="suggestion-icon">
                    {suggestion.includes('hotel') ? '🏨' : 
                     suggestion.includes('restaurant') ? '🍽️' :
                     suggestion.includes('laptop') || suggestion.includes('phone') ? '💻' : '🔍'}
                  </span>
                  {suggestion}
                </button>
              ))}
            </div>

            {/* Quick Actions */}
            <div className="quick-actions">
              <button onClick={() => handleSuggestionClick("Best restaurants near me")} className="quick-action">
                🍽️ Best restaurants near me
              </button>
              <button onClick={() => handleSuggestionClick("Top hotels in my city")} className="quick-action">
                🏨 Top hotels in my city
              </button>
              <button onClick={() => handleSuggestionClick("Best laptops under $1000")} className="quick-action">
                💻 Best laptops under $1000
              </button>
            </div>

            {/* Extensions */}
            <div className="extensions-info">
              <span className="status-dot"></span>
              <span>Active extensions</span>
            </div>

            <div className="footer-info">
              <span>Unlock new era with Alpha AI. </span>
              <a href="#" className="share-link">share us</a>
            </div>
          </div>
        ) : (
          // Search Results Screen
          <div className="results-screen">
            {/* Search Bar at Top */}
            <div className="results-search-container">
              <div className="search-bar">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask anything..."
                  className="search-input"
                  disabled={isLoading}
                />
                <button 
                  onClick={startVoiceInput}
                  className={`voice-btn ${isListening ? 'listening' : ''}`}
                  disabled={isLoading}
                >
                  🎤
                </button>
              </div>
              {isLoading && <div className="loading-indicator">⚡ Searching...</div>}
            </div>

            {/* Response */}
            <div className="response-container">
              <div className="response-content">
                <h3>Alpha Response</h3>
                <div className="response-text">
                  <ReactMarkdown 
                    components={{
                      // Custom components for better styling
                      h1: ({children}) => <h1 className="response-h1">{children}</h1>,
                      h2: ({children}) => <h2 className="response-h2">{children}</h2>,
                      h3: ({children}) => <h3 className="response-h3">{children}</h3>,
                      ul: ({children}) => <ul className="response-ul">{children}</ul>,
                      ol: ({children}) => <ol className="response-ol">{children}</ol>,
                      li: ({children}) => <li className="response-li">{children}</li>,
                      p: ({children}) => <p className="response-p">{children}</p>,
                      strong: ({children}) => <strong className="response-strong">{children}</strong>,
                      code: ({children}) => <code className="response-code">{children}</code>,
                      blockquote: ({children}) => <blockquote className="response-blockquote">{children}</blockquote>
                    }}
                  >
                    {response}
                  </ReactMarkdown>
                </div>
              </div>

              {/* Follow-up Suggestions */}
              {suggestions.length > 0 && (
                <div className="followup-suggestions">
                  <h4>Follow-up questions:</h4>
                  <div className="suggestion-chips">
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="suggestion-chip"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Search History */}
            {searchHistory.length > 0 && (
              <div className="history-container">
                <h4>Recent Searches</h4>
                {searchHistory.slice(0, 3).map((item, index) => (
                  <div key={index} className="history-item">
                    <div className="history-query">{item.query}</div>
                    <div className="history-preview">
                      {item.response.substring(0, 100)}...
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default App;