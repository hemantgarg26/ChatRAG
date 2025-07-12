# NeuroChat

A full-stack chat application with AI-powered responses, built with FastAPI backend and React frontend.

## Overview

NeuroChat is a modern chat application that leverages AI to provide intelligent responses to user queries. The application consists of:

- **Backend (BE)**: FastAPI-based REST API with AI integration, vector embeddings, and asynchronous task processing
- **Frontend (FE)**: React.js web application with real-time chat interface

## Project Structure

```
ChatRAG/
├── BE/                 # Backend API (FastAPI)
├── FE/                 # Frontend Web App (React.js)
└── README.md           # This file
```

## Getting Started

### Backend Setup
For detailed backend setup instructions, configuration, and architecture details, see:
**[Backend README](BE/README.md)**

### Frontend Setup
For detailed frontend setup instructions, features, and API integration, see:
**[Frontend README](FE/README.md)**

## Quick Start

1. **Backend**: Navigate to `BE/` directory and follow the setup instructions in the Backend README
2. **Frontend**: Navigate to `FE/` directory and follow the setup instructions in the Frontend README

## Features

- 🤖 AI-powered chat responses
- 📱 Modern, responsive web interface
- 🔄 Asynchronous message processing
- 💾 Message history persistence
- 🎯 Vector-based similarity search
- 📊 Real-time status updates

## Technologies Used

### Backend
- FastAPI (Python web framework)
- MongoDB (Database)
- Redis (Message broker)
- Celery (Task queue)
- Pinecone (Vector database)
- OpenAI/GPT integration

### Frontend
- React.js
- Modern CSS with responsive design
- REST API integration
- Real-time polling mechanism
