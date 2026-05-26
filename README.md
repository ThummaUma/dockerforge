# DockerForge 

An AI-powered tool that automatically generates working Dockerfiles for any GitHub repository.

## Architecture
- Frontend: React.js
- Backend: FastAPI (Python)
- AI: Groq API (llama-3.3-70b-versatile)
- Docker SDK for building and verifying images

## Setup Instructions

### Requirements
- Python 3.9+
- Node.js 18+
- Docker Desktop

### Backend Setup
cd backend
pip install -r requirements.txt
create .env file with GROQ_API_KEY=your_key
uvicorn main:app --reload

### Frontend Setup
cd frontend
npm install
npm start

## LLM Provider
Used Groq API with llama-3.3-70b-versatile model.
Reason: Free tier available, fast response times.

## Known Limitations
- Only works with public GitHub repositories
- Build may fail for repos with complex dependencies
- Max 3 retry attempts for failed builds