# LexiGraph

LexiGraph is an AI-powered knowledge graph generator that transforms lecture content and educational text into interactive, visual concept maps. The application uses advanced AI models to analyze text content and generate structured knowledge graphs through a multi-agent processing pipeline.

## Features

- **Multi-AI Provider Support**: Works with Anthropic Claude, OpenAI GPT, and OpenRouter models
- **Intelligent Text Processing**: Multi-agent pipeline with specialized agents for validation, summarization, and visualization
- **Interactive Web Interface**: Modern React/Next.js frontend with real-time processing feedback
- **Graph Generation**: Automatically creates DOT format graphs and renders them as PNG images
- **Flexible Input**: Supports various text formats including lecture transcripts, educational content, and research papers

## Architecture

### Backend
- **Framework**: FastAPI with Python 3.13+
- **Core Pipeline**: Multi-agent system using LangChain
  - Validation Agent: Content classification and input filtering
  - Summarization Agent: Content analysis and structured summarization  
  - Visualization Agent: DOT code generation for graph visualization
- **Graph Processing**: Graphviz for DOT to PNG conversion
- **API**: RESTful endpoints with CORS support for frontend integration

### Frontend
- **Framework**: Next.js 15 with React 19
- **Styling**: Tailwind CSS with custom components
- **Form Management**: React Hook Form with Zod validation
- **API Communication**: Axios for HTTP requests
- **UI Components**: Radix UI primitives for accessibility

## Installation

### Prerequisites
- Python 3.13+
- Node.js 18+
- uv (Python package manager)
- Graphviz system package

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies using uv:
```bash
uv sync
```

3. Start the FastAPI server:
```bash
uv run python main.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000` with the API running on `http://localhost:8000`.

## Configuration

API keys are entered directly through the web interface when using the application. No additional configuration files are needed.

### Supported Models

#### Anthropic
- Claude Opus 4.1
- Claude Opus 4
- Claude Sonnet 4
- Claude Sonnet 3.7
- Claude Haiku 3.5

#### OpenAI
- GPT-5
- GPT-4.1
- GPT-4o
- GPT-4 Turbo

#### OpenRouter
- Access to various open-source and commercial models

## Usage

1. **Select AI Provider**: Choose from Anthropic, OpenAI, or OpenRouter
2. **Choose Model**: Select the specific model variant
3. **Enter API Key**: Provide your API key for the selected provider
4. **Input Text**: Paste or type the lecture content you want to analyze
5. **Generate Graph**: Click "Generate Graph" to process the content
6. **View Results**: Review the generated knowledge graph and summary

The system will validate the content, extract key concepts and relationships, and generate a visual knowledge graph showing the hierarchical structure and connections between concepts.

## API Endpoints

- `GET /` - Health check
- `GET /providers` - List available AI providers
- `GET /models/{provider}` - Get models for specific provider
- `POST /process` - Process text and generate knowledge graph
- `GET /graph/{filename}` - Retrieve generated graph image

## Development

### Project Structure
```
├── backend/              # FastAPI backend
│   ├── core/            # Core processing pipeline
│   │   ├── pipeline.py  # Multi-agent processing logic
│   │   └── utils.py     # Utility functions
│   └── main.py          # FastAPI application
├── frontend/            # Next.js frontend
│   └── src/
│       ├── app/         # Next.js app router
│       └── components/  # React components
└── output/              # Generated graph images
```

### Adding New AI Providers

1. Update the `get_llm_instance` function in `core/pipeline.py`
2. Add provider configuration in the frontend `ProviderSelector` component
3. Update the API key validation logic in `main.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.