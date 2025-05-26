# Local RAG MBSE Assistant 🏗️

A powerful Model-Based Systems Engineering (MBSE) assistant that leverages Local RAG (Retrieval-Augmented Generation) capabilities to provide context-aware responses within the Arcadia methodology framework. This tool helps systems engineers analyze and work with MBSE artifacts more effectively.

## Features 🚀

- **Arcadia Methodology Integration**: Built-in support for all Arcadia phases:
  - Operational Analysis
  - System Analysis
  - Logical Architecture
  - Physical Architecture
  - Verification & Validation
  - Traceability Analysis

- **Advanced Document Processing**:
  - Support for multiple file formats (.pdf, .docx, .txt, .xml, .json)
  - Special handling for MBSE files (.aird, .capella)
  - Intelligent chunking and context preservation

- **Local RAG System**:
  - Uses Ollama for local LLM inference
  - Efficient vector database storage with ChromaDB
  - Context-aware AI responses
  - Semantic search capabilities

- **Interactive Web Interface**:
  - Built with Streamlit
  - Phase-organized sample queries
  - Real-time response generation
  - User-friendly document upload

## Prerequisites 📋

- Python 3.8 or higher
- [Ollama](https://ollama.ai) installed and running
- Virtual environment management tools

## Installation 🛠️

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd local-rag-mbse
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Ollama:
   - Ensure Ollama is running
   - Update `config.py` with your Ollama server URL if needed
   - Default models: 
     - LLM: gemma:7b
     - Embeddings: nomic-embed-text

## Usage 💡

1. Start the application:
   ```bash
   python run_app.py
   ```

2. Access the web interface:
   - Open your browser and navigate to `http://localhost:8501`
   - The interface will be available with all features ready to use

3. Working with Documents:
   - Upload your MBSE documents through the web interface
   - The system will process and index them automatically
   - Use the query interface to ask questions about your documents

## Project Structure 📁

- `app.py`: Main Streamlit web application
- `config.py`: Configuration settings and constants
- `document_processor.py`: Document processing and indexing logic
- `rag_system.py`: RAG implementation and query handling
- `run_app.py`: Application runner script

## Configuration ⚙️

The system can be configured through `config.py`, including:
- Ollama model settings
- Vector database configuration
- Document processing parameters
- MBSE-specific settings
- Arcadia methodology configurations

## Supported File Types 📄

- `.pdf`: PDF documents
- `.docx`: Microsoft Word documents
- `.txt`: Plain text files
- `.xml`: XML model exports
- `.json`: JSON data files
- `.aird`: Arcadia representation files
- `.capella`: Capella project files

## Contributing 🤝

Contributions are welcome! Please feel free to submit pull requests or open issues for any improvements or bug fixes.

## License 📄

[Add your license information here] 