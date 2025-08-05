# Multi-Agent Travel Assistant 🚀

A CrewAI-based system that autonomously researches flights, makes bookings, and sends notifications using specialized AI agents.

## Features

- **Agent Orchestration**: Coordinates researcher, booker, and notifier agents
- **Dual LLM Support**: Works with both OpenAI API and local Ollama models
- **Mock APIs**: Built-in dummy APIs for testing
- **Task Chaining**: Automatic context passing between agents

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) (for local LLM option)
- OpenAI API key (for cloud option)

`
OPENAI_API_KEY=your_api_key_here

`
## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/multi-agent-travel.git
   cd multi-agent-travel