# Sigraph

**A knowledge base system that detects behavioral patterns from System Provenance using OpenTelemetry Traces**

```
    ________   ________   ________
   |        | |        | |        |
   |  ◉──┐  | |  ◉──┐  | |  ◉──┐  |
   |     │  | |     │  | |     │  |
   | sig1│──┼─┘ sig2│──┼─┘ sig3│──►
   |_____|  | |_____|  | |_____|   

      S    I    G    R    A    P    H
```

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [License](#license)

## Overview

Sigraph is an advanced knowledge graph system designed to analyze and detect behavioral patterns in system provenance data. It leverages OpenTelemetry traces, AI-powered analysis, and graph database technology to provide comprehensive insights into system behaviors, making it particularly useful for malware analysis, security research, and system behavior monitoring.

The system integrates multiple technologies:
- **Neo4j** for graph database storage and relationship modeling
- **OpenSearch** for log indexing and full-text search
- **AI/LLM integration** (Google Gemini, OpenAI, Ollama) for intelligent analysis
- **FastAPI** backend for robust API services
- **Streamlit** frontend for interactive user interface

## Features

- **System Provenance Tracking**: Captures and analyzes system calls and operations including:
  - Process actions (launch, remote thread, access, tampering)
  - Network operations (connect, accept)
  - File operations (create, rename, delete, modify, raw access)
  - Registry operations (add, delete, set, rename, query)

- **AI-Powered Analysis**: 
  - Natural language querying of system behavior data
  - Automated pattern detection using LLM models
  - Context-aware responses with supporting evidence
  - Multi-model support (Gemini, OpenAI, Ollama)

- **Graph-Based Storage**:
  - Relationship modeling between system entities
  - Efficient querying of complex behavioral patterns
  - Provenance tracking with artifact relationships

- **Real-time Monitoring**:
  - RESTful API for event ingestion
  - Health and readiness endpoints
  - Scalable architecture with Gunicorn deployment

- **Interactive Interface**:
  - Streamlit-based web UI for querying and visualization
  - Chat-like interface for natural language questions
  - Context display for transparency in AI responses

## Architecture

Sigraph follows a microservices architecture with three main components:

```
┌─────────────────┐
│  Streamlit UI   │ (Port 8501)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Server │ (Port 8765)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌────────────┐
│  Neo4j  │ │ OpenSearch │
│  Graph  │ │   Logs     │
└─────────┘ └────────────┘
```

### Components:

1. **Backend (FastAPI)**: Handles API requests, processes system call data, and manages AI interactions
2. **Graph Database (Neo4j)**: Stores system provenance as a graph with nodes and relationships
3. **Search Engine (OpenSearch)**: Indexes and searches system logs
4. **Frontend (Streamlit)**: Provides an interactive web interface for users
5. **AI Agent**: Integrates with LLM providers for intelligent analysis

## Prerequisites

- **Docker** and **Docker Compose** (recommended for deployment)
- **Python 3.13+** (for local development)
- **Neo4j 5.x** compatible database
- **OpenSearch 2.13+** compatible instance
- **API Keys** for AI services (optional, based on chosen model):
  - Google Gemini API key
  - OpenAI API key
  - Or local Ollama installation

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/hongsam14/sigraph.git
cd sigraph
```

2. Copy the environment sample file:
```bash
cp env.sample .env
```

3. Edit `.env` file with your configuration (see [Configuration](#configuration))

4. Create required volume directories:
```bash
mkdir -p volume/{logs,config,data,plugins,opensearch,app-logs}
```

5. Start the services:
```bash
docker-compose up -d
```

6. Access the applications:
   - Neo4j Browser: http://localhost:7474
   - OpenSearch Dashboards: http://localhost:5601
   - FastAPI Backend: http://localhost:8765
   - FastAPI Docs: http://localhost:8765/docs
   - Streamlit UI: (run separately, see below)

### Running Streamlit UI

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run src/streamlit_app.py
```

The UI will be available at http://localhost:8501

### Local Development Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp env.sample .env
# Edit .env with your local configuration
```

3. Run Neo4j and OpenSearch locally or via Docker

4. Start the FastAPI backend:
```bash
python src/backend_app.py
```

5. Start the Streamlit frontend:
```bash
streamlit run src/streamlit_app.py
```

## Configuration

Edit the `.env` file to configure the application:

```env
# Neo4j Configuration
NEO4J_URI=neo4j              # or localhost for local development
NEO4J_USER=neo4j
NEO4J_PASSWORD=ChangeMe12#$  # Change to a secure password

# OpenSearch Configuration
OPENSEARCH_URI=opensearch     # or localhost for local development
OPENSEARCH_INDEX=syslog_index

# Backend Configuration
BACKEND_URI=0.0.0.0
BACKEND_PORT=8765

# AI Configuration (Optional - choose your preferred model)
# AI_MODEL="gemini-1.5-flash"
# AI_MODEL="gpt-4o-mini"
# AI_REALTIME_MODEL="gpt-4o-mini"
# AI_CHUNK_SIZE=400
# AI_OVERLAP=40
# AI_API_KEY='your-api-key-here'
```

### Configuration Options:

- **NEO4J_URI**: Neo4j database URI (use service name in Docker, localhost otherwise)
- **NEO4J_USER**: Neo4j username
- **NEO4J_PASSWORD**: Neo4j password
- **OPENSEARCH_URI**: OpenSearch instance URI
- **OPENSEARCH_INDEX**: Index name for system logs
- **BACKEND_URI**: Backend server host
- **BACKEND_PORT**: Backend server port
- **AI_MODEL**: LLM model to use (gemini-1.5-flash, gpt-4o-mini, etc.)
- **AI_API_KEY**: API key for your chosen LLM provider
- **AI_CHUNK_SIZE**: Text chunk size for document processing
- **AI_OVERLAP**: Overlap size between chunks

## Usage

### 1. Using the Streamlit Interface

1. Access the Streamlit UI at http://localhost:8501
2. Enter the backend URL (default: http://localhost:8765)
3. Type natural language questions about system behavior:
   - "What processes were launched?"
   - "Show me all network connections"
   - "What files were modified?"
4. Toggle "Show context" to see supporting evidence for AI responses

### 2. Using the API

#### Post a System Call Event

```bash
curl -X POST http://localhost:8765/v1/db/syscall \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "abc123",
    "span_id": "span456",
    "actor": {
      "type": "PROCESS",
      "name": "explorer.exe",
      "uuid": "proc-uuid-123"
    },
    "action": "LAUNCH",
    "artifact": {
      "type": "PROCESS",
      "name": "cmd.exe",
      "uuid": "proc-uuid-456"
    }
  }'
```

#### Query the Knowledge Graph

```bash
curl -X POST http://localhost:8765/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What malicious behavior patterns were detected?"
  }'
```

#### Health Check

```bash
# Liveness probe
curl http://localhost:8765/healthz

# Readiness probe
curl http://localhost:8765/readyz
```

## API Documentation

Once the FastAPI backend is running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc

### Main API Endpoints:

#### Database API (`/v1/db`)
- `POST /v1/db/syscall` - Store system call events in the graph database
- `GET /v1/db/events` - Retrieve stored events
- `POST /v1/db/syslog` - Store system logs in OpenSearch

#### AI API (`/v1/ai`)
- `POST /v1/ai/query` - Query the knowledge graph using natural language
- `POST /v1/ai/report` - Submit a report for analysis and graph conversion
- `GET /v1/ai/entities` - Extract entities from a question

#### Health Endpoints
- `GET /healthz` - Liveness probe
- `GET /readyz` - Readiness probe

## Project Structure

```
sigraph/
├── docker-compose.yml          # Docker services configuration
├── env.sample                  # Sample environment variables
├── requirements.txt            # Python dependencies
├── LICENSE                     # GPL-2.0 license
├── README.md                   # This file
├── neo4j/                      # Neo4j Docker configuration
├── volume/                     # Persistent data volumes
│   ├── logs/                   # Neo4j logs
│   ├── data/                   # Neo4j data
│   ├── config/                 # Neo4j config
│   ├── plugins/                # Neo4j plugins
│   ├── opensearch/             # OpenSearch data
│   └── app-logs/               # Application logs
└── src/                        # Source code
    ├── Dockerfile              # FastAPI container
    ├── backend_app.py          # FastAPI application entry point
    ├── streamlit_app.py        # Streamlit UI entry point
    ├── gunicorn.conf.py        # Gunicorn configuration
    ├── app/                    # Application modules
    │   ├── config.py           # Configuration management
    │   ├── backend/            # Backend API
    │   │   ├── api.py          # Main API router
    │   │   └── v1/             # API version 1
    │   │       └── api.py      # V1 endpoints
    │   └── streamlit/          # Streamlit utilities
    │       └── utils.py        # UI helper functions
    ├── ai/                     # AI integration
    │   ├── ai_agent.py         # Main AI agent
    │   ├── ai_court.py         # AI deliberation system
    │   ├── prompt.py           # LLM prompts
    │   └── output_format.py    # Output schemas
    ├── db/                     # Database layer
    │   ├── db_session.py       # OpenSearch session
    │   ├── db_model.py         # Data models
    │   └── exceptions.py       # DB exceptions
    └── graph/                  # Graph database layer
        ├── graph_session.py    # Neo4j session management
        ├── graph_model.py      # Graph data models
        ├── graph_client/       # Neo4j client
        │   ├── client.py       # Graph client implementation
        │   └── node.py         # Node/relationship abstractions
        ├── graph_element/      # Graph elements
        │   ├── element.py      # Node and edge definitions
        │   ├── schema.py       # Graph schemas
        │   └── helper.py       # Helper functions
        └── provenance/         # System provenance types
            ├── type.py         # Action and artifact types
            ├── type_extension.py # Type extensions
            └── tests/          # Unit tests
```

## Technology Stack

### Backend
- **Python 3.13**: Primary programming language
- **FastAPI**: Modern, high-performance web framework
- **Uvicorn/Gunicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and settings management

### Database & Storage
- **Neo4j 5.x**: Graph database for provenance tracking
- **OpenSearch 2.13**: Search and analytics engine
- **py2neo**: Neo4j Python driver
- **opensearch-py**: OpenSearch Python client

### AI & Machine Learning
- **LangChain**: LLM application framework
- **Google Generative AI**: Gemini models integration
- **OpenAI**: GPT models integration
- **Ollama**: Local LLM support
- **LangChain Neo4j**: Graph-based RAG (Retrieval-Augmented Generation)

### Frontend
- **Streamlit**: Interactive web UI framework
- **Altair**: Declarative statistical visualization

### DevOps & Deployment
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Git**: Version control

### Development Tools
- **Pylint**: Code linting
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **isort**: Import sorting

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines:
- Follow PEP 8 style guide
- Add type hints to function signatures
- Write docstrings for modules, classes, and functions
- Add tests for new features
- Run linters before committing: `pylint`, `mypy`, `bandit`

## License

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Neo4j for graph database capabilities
- Powered by LangChain for AI integration
- UI created with Streamlit
- Inspired by system provenance and security research

---

**Note**: This project is designed for security research and malware analysis. Use responsibly and in accordance with applicable laws and regulations.
