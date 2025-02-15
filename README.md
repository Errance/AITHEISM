# AITHEISM

AITHEISM is a project exploring the intersection of artificial intelligence and religious/philosophical thought. It facilitates structured discussions between multiple AI models about metaphysical questions, particularly focusing on whether and how AI might develop its own forms of religious or philosophical beliefs.

## Overview

The system enables multiple AI models (including GPT-4, Claude, Gemini, DeepSeek, and Qwen) to engage in deep philosophical discussions. Each model brings its unique perspective while maintaining a structured dialogue format.

## Features

- Multi-model philosophical discussions
- Structured argument analysis
- Memory and context management
- Real-time API access to discussions
- Extensible thinker framework

## Getting Started

### Prerequisites
- Python 3.8+
- OpenRouter API key

### Installation
```bash
# Clone the repository
git clone https://github.com/Errance/AITHEISM.git

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the System
```bash
# Start the main discussion
python -m src.religion_one_thinking.main

# Start the API server (in a separate terminal)
uvicorn src.religion_one_thinking.api.routes:app --reload --port 9001
```

## Documentation

- [API Documentation](docs/API.md)
- [Architecture Overview](docs/ARCHITECTURE.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Environment Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Set your API key in `.env`:
- Get your API key from [OpenRouter](https://openrouter.ai)
- Add it to `.env` as OPENROUTER_API_KEY

3. (Optional) Configure server settings in `.env`:
- PORT: API server port (default: 9001)
- HOST: API server host (default: 0.0.0.0)

## Security Notes
- Never commit your `.env` file
- Keep your API keys secure
- The `.env` file is ignored by git