import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const chatAPI = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Get chat messages with pagination
export const getChat = async (userId, pageNumber = 1) => {
  try {
    const response = await chatAPI.get(`/api/chat/getChat`, {
      params: {
        user_id: userId,
        page_number: pageNumber,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching chat messages:', error);
    throw error;
  }
};

// Send a message to the system
export const sendMessage = async (userId, message) => {
  try {
    const response = await chatAPI.post('/api/chat/sendMessage', {
      user_id: userId,
      message: message,
    });
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

// Get message status for polling
export const getMessagesStatus = async (userId, messageIds) => {
  try {
    const response = await chatAPI.post('/api/chat/getMessagesStatus', {
      user_id: userId,
      message_ids: messageIds,
    });
    return response.data;
  } catch (error) {
    console.error('Error getting message status:', error);
    throw error;
  }
};

// Utility function to poll for message status
export const pollForMessageStatus = async (userId, messageId, maxRetries = 10, interval = 10000) => {
  return new Promise((resolve, reject) => {
    let retryCount = 0;
    
    const poll = async () => {
      try {
        const response = await getMessagesStatus(userId, [messageId]);
        
        if (response.status === 'success' && response.data.length > 0) {
          const messageStatus = response.data[0];
          
          // Check if message processing is complete
          if (messageStatus.status === 6) { // MESSAGE_PROCESSING_SUCCESS
            resolve(messageStatus);
            return;
          }
          
          // Check if message processing failed
          if (messageStatus.status === 7) { // PROCESSING_ERROR
            resolve(messageStatus);
            return;
          }
        }
        
        // Continue polling if not complete and retries left
        retryCount++;
        if (retryCount < maxRetries) {
          setTimeout(poll, interval);
        } else {
          reject(new Error('Polling timeout: Maximum retries reached'));
        }
      } catch (error) {
        retryCount++;
        if (retryCount < maxRetries) {
          setTimeout(poll, interval);
        } else {
          reject(error);
        }
      }
    };
    
    poll();
  });
}; 