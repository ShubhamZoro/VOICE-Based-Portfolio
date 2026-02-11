# Voice-Based Portfolio

A real-time voice-interactive portfolio application featuring an AI agent that represents **Shubham**. Users can have a natural voice conversation with the agent to learn about Shubham's background, skills, and experience. Link: https://voice-based-portfolio.onrender.com/

## Overview

This project implements a voice AI agent using **Deepgram** for low-latency Speech-to-Text (STT) and Text-to-Speech (TTS), and **OpenAI** for intelligence. It features a **RAG (Retrieval Augmented Generation)** system that allows the agent to answer questions accurately based on a provided knowledge base (e.g., a resume or portfolio document).

## Features

- **Real-time Voice Conversation:** Seamless, low-latency voice interaction with the AI agent.
- **RAG Integration:** The agent retrieves context from documents (DOCX/Text) to answer specific questions about Shubham.
- **Hybrid Search:** Supports both OpenAI dense embeddings and a sparse (Bag-of-Words) fallback for document retrieval.
- **Deepgram Aura:** Utilizes Deepgram's Aura-2 model for high-quality, natural-sounding speech synthesis.
- **WebSocket Communication:** Uses Flask-SocketIO for efficient, real-time audio streaming between the client and server.
- **Conversation Management:** Handles interruptions, fillers ("Let me check..."), and conversation endings gracefully.

## Tech Stack

- **Backend:** Python, Flask, Flask-SocketIO
- **Frontend:** HTML/JS (served via Flask templates)
- **AI Services:** 
  - **Deepgram:** STT (Nova-2/3), TTS (Aura-2)
  - **OpenAI:** GPT-4o-mini (LLM), Embeddings (text-embedding-3-small)
- **Concurrency:** Eventlet, Asyncio

## Prerequisites

- Python 3.10+
- [Deepgram API Key](https://console.deepgram.com/)
- [OpenAI API Key](https://platform.openai.com/)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd VOICE-Based-Portfolio
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables:**
   Create a `.env` file in the root directory (or set them in your environment):
   ```
   DEEPGRAM_API_KEY=your_deepgram_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

   *Note: `OPENAI_API_KEY` is required if using OpenAI embeddings for RAG. If not provided, the system falls back to keyword matching.*

4. **Prepare Knowledge Base:**
   Place your portfolio document (e.g., `resume.docx` or `portfolio.txt`) in the `docs/` directory (or as configured in `common/config.py`).

## Usage

1. **Run the Application:**
   ```bash
   python app.py
   ```
   *Alternatively, `main.py` or `client.py` can be used, but `app.py` is the recommended entry point.*

2. **Access the Interface:**
   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

3. **Start Talking:**
   Click the "Start" or microphone button on the web interface and start asking questions about Shubham!

## Configuration

Configuration settings can be modified in `common/config.py` and `common/agent_templates.py`:
- **Voice Model:** Default is `aura-2-apollo-en`.
- **Prompt:** Defined in `common/prompt_templates.py`.
- **RAG Settings:** Chunk size, overlap, and embedding model can be tweaked in `common/config.py`.

## License

[MIT](LICENSE)
