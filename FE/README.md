# Neuro Chat Frontend

A simple React.js chat interface that connects to the Neuro Chat backend API.

## Features

- **Real-time Chat Interface**: Clean, modern chat UI with message bubbles
- **Message History**: Loads previous chat messages on startup
- **Async Message Processing**: Sends messages and polls for AI responses
- **Status Indicators**: Shows processing status and completion states
- **Responsive Design**: Works on desktop and mobile devices
- **Auto-scroll**: Automatically scrolls to latest messages

## Architecture

The frontend implements the following flow:

1. **Load Chat History**: Fetches existing messages via `GET /api/chat/getChat`
2. **Send Message**: Submits user message via `POST /api/chat/sendMessage`
3. **Poll for Response**: Monitors message status via `POST /api/chat/getMessagesStatus`
4. **Update UI**: Displays system response when processing completes

## Setup Instructions

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn package manager
- Backend API running on port 8000

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   Create a `.env` file in the root directory:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

3. **Start the development server**:
   ```bash
   npm start
   ```

4. **Open the application**:
   Navigate to `http://localhost:3000` in your browser

### Building for Production

```bash
npm run build
```

This creates a `build` directory with optimized production files.

## Configuration

### Environment Variables

- `REACT_APP_API_URL`: Backend API base URL (default: `http://localhost:8000`)

### User ID

The application uses a hardcoded user ID for simplicity:
- User ID: `68714a69df9144af1173a76b`

To change this, modify the `USER_ID` constant in `src/components/Chat.js`.

## API Integration

The frontend communicates with three backend endpoints:

### 1. Get Chat History
```
GET /api/chat/getChat?user_id={userId}&page_number={pageNumber}
```

### 2. Send Message
```
POST /api/chat/sendMessage
Body: { "user_id": "string", "message": "string" }
```

### 3. Get Message Status
```
POST /api/chat/getMessagesStatus
Body: { "user_id": "string", "message_ids": ["string"] }
```

## Polling Mechanism

The application implements a polling system for message responses:

- **Max Retries**: 10 attempts
- **Interval**: 10 seconds between polls
- **Timeout**: Stops polling after 100 seconds (10 × 10s)

## File Structure

```
FE/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── api/
│   │   └── chatService.js  # API communication functions
│   ├── components/
│   │   ├── Chat.js         # Main chat component
│   │   └── Chat.css        # Chat component styles
│   ├── App.js              # Main application component
│   ├── App.css             # Application styles
│   ├── index.js            # React entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
└── README.md               # This file
```

## Styling

The application uses modern CSS with:

- **Gradient backgrounds** for visual appeal
- **Flexbox layout** for responsive design
- **Smooth animations** for loading states
- **Custom scrollbars** for better UX
- **Mobile-first responsive design**

## Troubleshooting

### Common Issues

1. **Connection Error**: Ensure backend is running on port 8000
2. **CORS Issues**: Backend has CORS enabled for all origins
3. **User Not Found**: Check if user exists in backend database
4. **Polling Timeout**: Increase retry count or interval in `chatService.js`

### Debug Mode

Open browser developer tools (F12) to see:
- Network requests to backend
- Console logs for debugging
- Error messages and stack traces

## Development Notes

- **Hardcoded User ID**: For simplicity, no authentication is implemented
- **Error Handling**: Basic error handling with user-friendly messages
- **State Management**: Uses React hooks (useState, useEffect)
- **No Backend Dependency**: Gracefully handles backend unavailability

## Future Enhancements

Potential improvements:

- User authentication and registration
- Multiple chat rooms/conversations
- File upload support
- Real-time updates with WebSockets
- Message search and filtering
- Typing indicators
- Message reactions and replies 