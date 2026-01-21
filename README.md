# GPR Defect Analysis Agent

Natural language interface for querying road infrastructure defect data using AI.

## Features
- 🤖 Text-to-SQL agent powered by Claude Sonnet
- 💬 Interactive chat interface
- 📊 Real-time analytics dashboard
- 🔍 Query history tracking
- 📈 Data visualizations

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
```bash
# Get key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY='your-key-here'
```

### 3. Create Database
```bash
python database_setup.py
```

### 4. Run Agent (CLI)
```bash
python gpr_agent.py
```

### 5. Run Web Interface
```bash
streamlit run app.py
```

## Architecture
- **LangChain**: Agent orchestration
- **Claude Sonnet 4**: Natural language understanding
- **SQLite**: Database storage
- **Streamlit**: Web interface

## Example Queries
- "How many defects are in the database?"
- "Show me all critical cavities in Gangnam-daero"
- "What's the average repair cost by defect type?"
- "Which locations have the most pending repairs?"