# Sigraph - Malware Knowledge Graph

```
    ________   ________   ________
   |        | |        | |        |
   |  ◉──┐  | |  ◉──┐  | |  ◉──┐  |
   |     │  | |     │  | |     │  |
   | sig1│──┼─┘ sig2│──┼─┘ sig3│──►
   |_____|  | |_____|  | |_____|   

      S    I    G    R    A    P    H


```

A knowledge graph-based system for detecting and analyzing behavioral patterns from System Provenance OpenTelemetry (Otel) Traces. Sigraph leverages AI agents and graph databases to provide intelligent malware analysis and threat detection capabilities.

## 🎯 Features

- **System Provenance Graph**: Build and analyze relationships between system events using Neo4j graph database
- **AI-Powered Analysis**: Integrate with multiple AI models (Google Gemini, OpenAI GPT, Ollama) for intelligent threat analysis
- **Behavioral Pattern Detection**: Detect malicious behavioral patterns from system call traces
- **Vector Search**: Advanced RAG (Retrieval Augmented Generation) capabilities for knowledge graph queries
- **OpenTelemetry Integration**: Process system provenance data from Otel traces
- **Multi-Modal Storage**: Combine graph database (Neo4j) with document search (OpenSearch)
- **REST API**: FastAPI-based backend for easy integration
- **Interactive UI**: Streamlit-based chat interface for querying malware reports
- **Docker Support**: Fully containerized deployment with Docker Compose

## 🏗️ Architecture

The system consists of four main components:

1. **Neo4j Graph Database**: Stores system provenance graph with APOC plugin support
2. **OpenSearch**: Document store for syslog data with full-text search capabilities
3. **FastAPI Backend**: RESTful API server for data ingestion and querying
4. **Streamlit Frontend**: Interactive chat interface for malware analysis

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  FastAPI Backend │────▶│  Neo4j Graph DB │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               │
                               ▼
                        ┌──────────────┐
                        │  OpenSearch  │
                        └──────────────┘
```

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.13+ (for local development)
- API keys for AI models (Google Gemini, OpenAI, or Ollama setup)

## 🚀 Installation

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/enki-polvo/malware-knowledge-graph.git
   cd malware-knowledge-graph
   ```

2. **Create environment file**
   ```bash
   cp env.sample .env
   ```

3. **Edit `.env` file with your configuration**
   ```bash
   # Required settings
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=YourSecurePassword123#
   
   # AI Model configuration (choose one)
   AI_MODEL=gemini-1.5-flash
   # AI_MODEL=gpt-4o-mini
   # AI_MODEL=gpt-oss-120b
   
   AI_API_KEY=your_api_key_here
   AI_CHUNK_SIZE=400
   AI_OVERLAP=40
   ```

4. **Create required volume directories**
   ```bash
   mkdir -p volume/{logs,config,data,plugins,opensearch,app-logs}
   ```

5. **Start the services**
   ```bash
   docker-compose up -d
   ```

6. **Verify services are running**
   ```bash
   docker-compose ps
   ```

### Local Development Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   export NEO4J_URI=localhost
   export NEO4J_USER=neo4j
   export NEO4J_PASSWORD=YourPassword
   export OPENSEARCH_URI=localhost
   export BACKEND_URI=localhost
   export BACKEND_PORT=8765
   ```

3. **Run the backend server**
   ```bash
   cd src
   python backend_app.py
   ```

4. **Run the Streamlit UI** (in a separate terminal)
   ```bash
   cd src
   streamlit run streamlit_app.py
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEO4J_URI` | Neo4j database URI | `neo4j` | Yes |
| `NEO4J_USER` | Neo4j username | `neo4j` | Yes |
| `NEO4J_PASSWORD` | Neo4j password | - | Yes |
| `OPENSEARCH_URI` | OpenSearch URI | `opensearch` | Yes |
| `OPENSEARCH_INDEX` | OpenSearch index name | `syslog_index` | Yes |
| `BACKEND_URI` | Backend server host | `0.0.0.0` | Yes |
| `BACKEND_PORT` | Backend server port | `8765` | Yes |
| `AI_MODEL` | AI model to use | - | Optional |
| `AI_REALTIME_MODEL` | Real-time AI model | - | Optional |
| `AI_CHUNK_SIZE` | Text chunk size for AI | `400` | Optional |
| `AI_OVERLAP` | Overlap size for chunks | `40` | Optional |
| `AI_API_KEY` | API key for AI service | - | Optional |

### Ports

- **7474**: Neo4j Browser (HTTP)
- **7687**: Neo4j Bolt protocol
- **9200**: OpenSearch REST API
- **5601**: OpenSearch Dashboards
- **8765**: FastAPI Backend

## 📖 Usage

### Starting the System

```bash
docker-compose up -d
```

### Accessing the Interfaces

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8765/docs
- **Neo4j Browser**: http://localhost:7474
- **OpenSearch Dashboards**: http://localhost:5601

### API Examples

#### 1. Post System Call Event

```bash
curl -X POST "http://localhost:8765/api/v1/db/syscall" \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace123",
    "span_id": "span456",
    "unit_id": "550e8400-e29b-41d4-a716-446655440000",
    "system_provenance": "PROCESS_LAUNCH",
    "timestamp": "2024-01-01T12:00:00Z",
    "weight": 1,
    "process_name": "malicious.exe"
  }'
```

#### 2. Post Syslog Data

```bash
curl -X POST "http://localhost:8765/api/v1/db/syslog" \
  -H "Content-Type: application/json" \
  -d '[{
    "unit_id": "550e8400-e29b-41d4-a716-446655440000",
    "trace_id": "trace123",
    "timestamp": "2024-01-01T12:00:00Z",
    "message": "Process execution detected"
  }]'
```

#### 3. Query System Provenance

```bash
curl -X GET "http://localhost:8765/api/v1/db/unit/550e8400-e29b-41d4-a716-446655440000/provenance"
```

#### 4. Analyze Behavior with AI

```bash
curl -X POST "http://localhost:8765/api/v1/ai/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What malicious behaviors were detected in trace123?"
  }'
```

#### 5. Get Syslog Sequence

```bash
curl -X GET "http://localhost:8765/api/v1/db/syslog/sequence/550e8400-e29b-41d4-a716-446655440000/trace123"
```

### Using the Streamlit Interface

1. Navigate to http://localhost:8501
2. Enter your query in the chat input (e.g., "What suspicious network activities were detected?")
3. View the AI-generated response with supporting context
4. Toggle "Show context" to see the retrieved knowledge graph data

## 📁 Project Structure

```
malware-knowledge-graph/
├── src/
│   ├── ai/                      # AI agent modules
│   │   ├── ai_agent.py          # Main AI agent with LangChain integration
│   │   ├── ai_court.py          # Multi-agent debate system
│   │   ├── output_format.py     # Response formatting
│   │   └── prompt.py            # AI prompts for different stages
│   ├── app/
│   │   ├── backend/             # FastAPI backend
│   │   │   ├── api.py           # Main API router
│   │   │   └── v1/
│   │   │       └── api.py       # V1 API endpoints (DB & AI)
│   │   ├── streamlit/           # Streamlit frontend
│   │   │   └── utils.py         # UI utilities
│   │   └── config.py            # Application configuration
│   ├── db/                      # Database layer
│   │   ├── db_model.py          # Syslog data models
│   │   ├── db_session.py        # OpenSearch session manager
│   │   └── exceptions.py        # Database exceptions
│   ├── graph/                   # Graph database layer
│   │   ├── graph_model.py       # Graph node models
│   │   ├── graph_session.py     # Neo4j session manager
│   │   ├── graph_client/        # Graph query client
│   │   ├── graph_element/       # Graph element definitions
│   │   └── provenance/          # System provenance types
│   ├── backend_app.py           # FastAPI application entry point
│   ├── streamlit_app.py         # Streamlit application entry point
│   ├── Dockerfile               # Backend container definition
│   └── gunicorn.conf.py         # Gunicorn configuration
├── neo4j/
│   ├── Dockerfile               # Neo4j with APOC plugin
│   └── apoc-5.22.0-core.jar     # APOC plugin JAR
├── volume/                      # Docker volumes (gitignored)
├── docker-compose.yml           # Multi-container orchestration
├── requirements.txt             # Python dependencies
├── env.sample                   # Environment variables template
└── README.md                    # This file
```

## 🛠️ Technologies

### Backend
- **FastAPI**: Modern, high-performance web framework
- **Uvicorn/Gunicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and settings management
- **Loguru**: Advanced logging library

### Database & Storage
- **Neo4j 5.x**: Graph database with APOC plugin
- **OpenSearch 2.13**: Search and analytics engine
- **py2neo**: Neo4j Python driver
- **opensearch-py**: OpenSearch Python client

### AI & Machine Learning
- **LangChain**: Framework for LLM application development
- **LangChain Neo4j**: Neo4j integration for LangChain
- **Google Gemini**: AI model integration (via langchain-google-genai)
- **OpenAI**: GPT model integration (via langchain-openai)
- **Ollama**: Local LLM support (via langchain-ollama)
- **Vector Stores**: Neo4jVector for embedding-based retrieval

### Frontend
- **Streamlit**: Interactive web UI framework
- **Altair**: Declarative visualization library

### DevOps
- **Docker & Docker Compose**: Containerization and orchestration
- **Python-dotenv**: Environment variable management

## 🔒 Security Considerations

1. **Change default passwords**: Always update the `NEO4J_PASSWORD` in production
2. **API Keys**: Store AI API keys securely and never commit them to version control
3. **Network isolation**: Use Docker networks to isolate services
4. **HTTPS**: Consider using a reverse proxy (nginx/traefik) for HTTPS in production
5. **OpenSearch security**: The current setup disables security plugins for development; enable them in production

## 🧪 Testing

Run the existing tests:

```bash
python -m pytest src/graph/provenance/tests/
```

## 📊 System Provenance Types

The system supports various provenance action types:

### Process Actions
- `LAUNCH`: Process creation
- `REMOTE_THREAD`: Remote thread injection
- `ACCESS`: Process access
- `TAMPERING`: Process tampering

### Network Actions
- `CONNECT`: Network connection
- `ACCEPT`: Accepting network connection

### File Actions
- `CREATE`: File creation
- `RENAME`: File rename
- `DELETE`: File deletion
- `MODIFY`: File modification
- `RAW_ACCESS_READ`: Raw disk access

### Registry Actions
- `REG_ADD`: Add registry key
- `REG_DELETE`: Delete registry key
- `REG_SET`: Set registry value
- `REG_RENAME`: Rename registry key
- `REG_QUERY`: Query registry

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Neo4j APOC library for graph algorithms
- LangChain for LLM orchestration framework
- OpenSearch for powerful search capabilities

## 📞 Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

---

**Note**: This project is designed for malware analysis and threat detection research. Use responsibly and in accordance with applicable laws and regulations.
