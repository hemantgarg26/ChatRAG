import React, { useState, useEffect, useRef } from 'react';
import { getChat, sendMessage, pollForMessageStatus } from '../api/chatService';
import './Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [processingMessages, setProcessingMessages] = useState(new Set());
  const messagesEndRef = useRef(null);
  
  // Hardcoded user ID as requested
  const USER_ID = '68714a69df9144af1173a76b'; // Example MongoDB ObjectId format

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history on component mount
  useEffect(() => {
    loadChatHistory();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      setIsLoadingHistory(true);
      const response = await getChat(USER_ID, 1);
      
      if (response.status === 'ok' && response.data) {
        setMessages(response.data);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      // Set empty messages if there's an error (user might not exist yet)
      setMessages([]);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const messageText = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    try {
      // Send message to backend
      const response = await sendMessage(USER_ID, messageText);
      
      if (response.status === 'success') {
        const messageId = response.message_id;
        
        // Add the user message to the UI immediately
        const newMessage = {
          id: messageId,
          user_message: messageText,
          system_message: '',
          system_message_status: 5, // MESSAGE_UNDER_PROCESSING
          timestamp: new Date().toISOString(),
        };
        
        setMessages(prev => [...prev, newMessage]);
        setProcessingMessages(prev => new Set(prev).add(messageId));
        
        // Start polling for response
        try {
          const messageStatus = await pollForMessageStatus(USER_ID, messageId);
          
          // Update the message with the system response
          setMessages(prev => 
            prev.map(msg => 
              msg.id === messageId 
                ? { 
                    ...msg, 
                    system_message: messageStatus.system_response || 'No response received',
                    system_message_status: messageStatus.status 
                  }
                : msg
            )
          );
        } catch (pollError) {
          console.error('Polling error:', pollError);
          // Update message with error state
          setMessages(prev => 
            prev.map(msg => 
              msg.id === messageId 
                ? { 
                    ...msg, 
                    system_message: 'Failed to get response. Please try again.',
                    system_message_status: 7 // PROCESSING_ERROR
                  }
                : msg
            )
          );
        } finally {
          setProcessingMessages(prev => {
            const newSet = new Set(prev);
            newSet.delete(messageId);
            return newSet;
          });
        }
      } else {
        alert('Failed to send message. Please try again.');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Error sending message. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getMessageStatusText = (status) => {
    switch (status) {
      case 5: return 'Processing...';
      case 6: return 'Completed';
      case 7: return 'Error';
      default: return 'Unknown';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (isLoadingHistory) {
    return (
      <div className="chat-container">
        <div className="chat-header">
          <h1>Neuro Chat</h1>
        </div>
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <p>Loading chat history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Neuro Chat</h1>
        <p className="user-id">User ID: {USER_ID}</p>
      </div>
      
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="no-messages">
            <p>No messages yet. Start a conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="message-group">
              <div className="message user-message">
                <div className="message-content">
                  <strong>You:</strong> {message.user_message}
                </div>
                <div className="message-timestamp">
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
              
              {message.system_message || processingMessages.has(message.id) ? (
                <div className="message system-message">
                  <div className="message-content">
                    <strong>System:</strong> {
                      processingMessages.has(message.id) 
                        ? 'Processing your message...' 
                        : message.system_message
                    }
                  </div>
                  <div className="message-status">
                    Status: {getMessageStatusText(message.system_message_status)}
                    {processingMessages.has(message.id) && (
                      <span className="processing-indicator">●</span>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input">
        <div className="input-group">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here..."
            disabled={isLoading}
            rows="3"
          />
          <button 
            onClick={handleSendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat; 