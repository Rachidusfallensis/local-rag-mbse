import os

# Ollama Configuration
OLLAMA_BASE_URL = "http://chat-eva.univ-pau.fr:11434"
DEFAULT_MODEL = "gemma:7b"
EMBEDDING_MODEL = "nomic-embed-text"

# Vector Database Configuration
VECTORDB_PATH = "./vectordb"
COLLECTION_NAME = "arcadia_mbse"

# Document Processing
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.xml', '.json', '.aird', '.capella']
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Streamlit Configuration
PAGE_TITLE = "MBSE Local RAG Assistant"
PAGE_ICON = "🏗️"

# Arcadia-specific settings
ARCADIA_NAMESPACES = {
    'capella': 'http://www.polarsys.org/capella/core',
    'requirement': 'http://www.polarsys.org/capella/requirements',
    'information': 'http://www.polarsys.org/capella/information'
}

# MBSE Analysis Context Types
MBSE_CONTEXT_TYPES = [
    "operational",
    "system", 
    "logical",
    "physical",
    "verification",
    "traceability"
]

# Arcadia Methodology Phase Descriptions
ARCADIA_PHASES = {
    "operational": {
        "name": "Operational Analysis",
        "description": "Understanding stakeholder needs and operational context",
        "icon": "🎭",
        "keywords": ["stakeholder", "actor", "operational", "capability", "mission", "goal"]
    },
    "system": {
        "name": "System Analysis", 
        "description": "Defining system requirements and functions",
        "icon": "⚙️",
        "keywords": ["function", "requirement", "interface", "system", "constraint", "mode"]
    },
    "logical": {
        "name": "Logical Architecture",
        "description": "Designing solution components and interfaces", 
        "icon": "🏗️",
        "keywords": ["component", "logical", "behavior", "interaction", "scenario", "exchange"]
    },
    "physical": {
        "name": "Physical Architecture",
        "description": "Implementing and deploying the solution",
        "icon": "🔧", 
        "keywords": ["physical", "implementation", "deployment", "node", "configuration", "hardware"]
    },
    "verification": {
        "name": "Verification & Validation",
        "description": "Approaches for system verification and validation",
        "icon": "✅",
        "keywords": ["verification", "validation", "test", "compliance", "trace", "coverage"]
    },
    "traceability": {
        "name": "Traceability Analysis", 
        "description": "Links between different architectural levels",
        "icon": "🔗",
        "keywords": ["trace", "link", "derive", "satisfy", "allocate", "refinement"]
    }
}

# Model capabilities and recommended uses
MODEL_RECOMMENDATIONS = {
    "codellama:13b": {
        "name": "CodeLlama 13B",
        "best_for": ["System modeling", "Architecture analysis", "Code generation"],
        "description": "Excellent for technical MBSE analysis and code-related queries"
    },
    "llama2:13b": {
        "name": "Llama2 13B", 
        "best_for": ["General analysis", "Requirements analysis", "Documentation"],
        "description": "Balanced performance for general MBSE questions"
    },
    "llama2:7b": {
        "name": "Llama2 7B",
        "best_for": ["Quick queries", "Basic analysis"],
        "description": "Faster responses for simple MBSE questions"
    },
    "mistral:7b": {
        "name": "Mistral 7B",
        "best_for": ["Structured analysis", "Technical documentation"], 
        "description": "Good for structured MBSE methodological questions"
    }
}

# File type specific processing settings
FILE_TYPE_SETTINGS = {
    ".capella": {
        "description": "Capella project files",
        "processor": "capella_project",
        "extract_elements": ["functions", "components", "requirements", "interfaces"]
    },
    ".aird": {
        "description": "Arcadia representation files", 
        "processor": "aird_archive",
        "extract_elements": ["model_elements", "diagrams", "properties"]
    },
    ".xml": {
        "description": "XML model exports",
        "processor": "xml_parser", 
        "extract_elements": ["requirements", "functions", "components", "interfaces"]
    }
}