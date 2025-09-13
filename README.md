# Canyon Code Agentic Query System 🏞️

~ Aditya Malwade (adityaint929@gmail.com)

An intelligent agentic system that enables analysts to query camera feed data, encoder configurations, and decoder settings using natural language. Built with LangGraph, Streamlit, and powered by Deepseek AI.

## 🎯 Overview

This system allows non-technical analysts to ask natural language questions about:

- **Camera Feeds**: 100 video streams with metadata (theater, codec, latency, resolution)
- **Encoder Configuration**: Video encoding parameters and settings
- **Decoder Configuration**: Video decoding parameters and settings
- **Schema Definitions**: Data structure and validation rules

## 🚀 Key Features

- **Natural Language Processing**: Ask questions in plain English
- **Agentic Workflow**: 2-node LangGraph system with intelligent tool selection
- **Real-time Analysis**: Live SQLite database queries
- **Configuration Management**: Access to JSON-based encoder/decoder settings
- **Interactive UI**: Modern Streamlit chat interface
- **Comprehensive Logging**: Full debugging and monitoring capabilities

## 🛠️ Technology Stack

- **AI/ML**: LangGraph, LangChain, Deepseek (via OpenRouter)
- **Backend**: Python, SQLite, SQLAlchemy
- **Frontend**: Streamlit
- **Data**: CSV ingestion, JSON configuration files

## 📊 Sample Queries

- _"What are the camera IDs capturing the pacific area with the best clarity?"_
- _"Show me the top 5 feeds with highest latency in PAC theater"_
- _"What preset is the encoder using and what's the current bitrate?"_
- _"Compare H264 vs H265 feeds performance"_

## 🏃‍♂️ Quick Start

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment**

   ```bash
   echo 'OPENROUTER_API_KEY="your_api_key_here"' > .env
   ```

3. **Initialize Database**

   ```bash
   python ingest_to_sqlite.py
   ```

4. **Launch Application**
   ```bash
   streamlit run app.py
   ```

## 📁 Project Structure

```
CanyonCode-HW/
├── data/                    # Data files (CSV, JSON)
├── canyon_code.db          # SQLite database
├── app.py                  # Streamlit UI
├── agent.py                # LangGraph agent
├── tools.py                # Agent tools
├── ingest_to_sqlite.py     # Data ingestion
└── requirements.txt        # Dependencies
```

## 🔧 Architecture

The system uses a 3-node LangGraph workflow:

1. **System Initialization**: Ensures proper context setup
2. **Agent Node**: Processes queries and decides on tool usage
3. **Tool Execution**: Executes SQL queries, parameter lookups, and schema checks

## 📈 Capabilities

- **SQL Query Generation**: Converts natural language to complex SQL
- **Multi-tool Coordination**: Seamlessly switches between different data sources
- **Error Handling**: Graceful handling of invalid queries and edge cases
- **Real-time Streaming**: Live response generation in the UI
- **Comprehensive Logging**: Full audit trail for debugging and monitoring
