# Religion One Architecture

## Overview
Religion One is a system designed to facilitate philosophical discussions between multiple AI models about religious and metaphysical topics. The system is built with a modular architecture that separates concerns and allows for easy extension.

## Core Components

### 1. Discussion System
- **Orchestrator**: Manages the overall discussion flow and coordinates between different AI models
- **Discussion Chain**: Maintains the sequence of discussion points and their relationships
- **Memory System**: Stores and retrieves discussion history and insights

### 2. Thinkers
Base classes and implementations for different AI models:
- `BaseThinker`: Abstract base class defining common interface
- Model-specific implementations:
  - `GPTThinker`: GPT-4 implementation
  - `ClaudeThinker`: Claude implementation
  - `GeminiThinker`: Gemini implementation
  - `DeepSeekThinker`: DeepSeek implementation
  - `QwenThinker`: Qwen implementation
  - `ContextProcessor`: Special thinker for processing discussion context

### 3. API Layer
- FastAPI-based REST API
- Endpoints for accessing discussion state and history
- Independent data reading and error handling

### 4. Storage System
- File-based storage for discussion data
- JSON format for data persistence
- Memory storage for AI insights

## Data Flow
1. Main program initializes discussion with a thesis
2. Orchestrator manages discussion rounds
3. Each thinker processes and responds to points
4. Responses are stored in discussion files
5. API layer provides access to stored data

## Directory Structure
```
src/religion_one_thinking/
├── api/
│   ├── routes.py
│   └── service.py
├── config/
│   └── config.yaml
├── discussion/
│   └── orchestrator.py
├── thinkers/
│   ├── base_thinker.py
│   ├── gpt_thinker.py
│   └── ...
├── utils/
│   ├── logger.py
│   └── discussion_manager.py
└── main.py
```

## Configuration
- Environment variables for API keys and sensitive data
- YAML configuration for system settings
- Logging configuration for debugging

## Extension Points
1. New AI models can be added by implementing `BaseThinker`
2. Additional API endpoints can be added in `routes.py`
3. Storage system can be extended to support different backends
4. Discussion flow can be modified in `orchestrator.py`

## Dependencies
- Python 3.8+
- FastAPI for API layer
- OpenAI/OpenRouter for AI model access
- Pydantic for data validation
- YAML for configuration
