import streamlit as st
import os
from pathlib import Path
from rag_system import LocalRAGSystem
import config
import json
from datetime import datetime
from diagram_generator import CapellaDiagramGenerator, DiagramType

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .chat-container {
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
    }
    .user-message {
        background-color: #e6f3ff;
        text-align: right;
    }
    .assistant-message {
        background-color: #f0f2f6;
    }
    .chat-input {
        border-radius: 20px;
        border: 1px solid #ddd;
    }
    .new-chat-button {
        border-radius: 20px;
        padding: 10px 20px;
    }
    .chat-list {
        max-height: 600px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Arcadia methodology reference links
ARCADIA_REFERENCES = {
    "Getting Started": "https://gettingdesignright.com/GDR-Educate/Capella_Tutorial_v6_0/GettingStarted.html",
    "Installation": "https://gettingdesignright.com/GDR-Educate/Capella_Tutorial_v6_0/GettingStarted.html#Installation",
    "Operational Analysis": "https://gettingdesignright.com/GDR-Educate/Capella_Tutorial_v6_0/OperationalAnalysis.html",
    "System Analysis": "https://gettingdesignright.com/GDR-Educate/Capella_Tutorial_v6_0/SystemAnalysis.html",
    "Logical Architecture": "https://gettingdesignright.com/GDR-Educate/Capella_Tutorial_v6_0/LogicalArchitecture.html",
    "Physical Architecture": "https://gettingdesignright.com/GDR-Educate/Capella_Tutorial_v6_0/PhysicalArchitecture.html"
}

# MBSE context prompts for better responses
MBSE_CONTEXT_PROMPTS = {
    "operational": "Focus on operational activities, actors, and capabilities from an Operational Analysis perspective.",
    "system": "Consider system functions, interfaces, and requirements from a System Analysis viewpoint.",
    "logical": "Analyze logical components, their interactions, and behavioral aspects from a Logical Architecture perspective.",
    "physical": "Examine physical components, deployment, and implementation from a Physical Architecture standpoint.",
    "verification": "Address verification and validation approaches for MBSE artifacts.",
    "traceability": "Consider traceability links between different architectural levels."
}

# Initialize RAG system
@st.cache_resource
def init_rag_system():
    return LocalRAGSystem()

def display_arcadia_references():
    """Display Arcadia methodology reference links"""
    st.sidebar.subheader("📚 Arcadia Methodology References")
    
    for phase, url in ARCADIA_REFERENCES.items():
        st.sidebar.markdown(f"• [{phase}]({url})")
    
    st.sidebar.info("💡 These links provide detailed guidance on each phase of the Arcadia methodology used in Capella.")

def get_enhanced_prompt(user_prompt, context_type=None):
    """Enhance user prompt with MBSE context"""
    if context_type and context_type in MBSE_CONTEXT_PROMPTS:
        enhanced_prompt = f"{MBSE_CONTEXT_PROMPTS[context_type]}\n\nUser Question: {user_prompt}"
        return enhanced_prompt
    return user_prompt

def load_chats():
    """Load saved chats from file"""
    chats_file = Path("saved_chats.json")
    if chats_file.exists():
        with open(chats_file, "r") as f:
            return json.load(f)
    return {}

def save_chats(chats):
    """Save chats to file"""
    with open("saved_chats.json", "w") as f:
        json.dump(chats, f)

def main():
    # Initialize session state
    if "chats" not in st.session_state:
        st.session_state.chats = load_chats()
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "rag_system" not in st.session_state:
        st.session_state.rag_system = init_rag_system()
    if "diagram_generator" not in st.session_state:
        st.session_state.diagram_generator = CapellaDiagramGenerator()

    # Layout
    st.title("🏗️ MBSE Assistant")
    
    # Chat Management
    col1, col2, col3 = st.columns([2, 6, 2])
    
    with col1:
        st.button("➕ New Chat", key="new_chat", 
                 on_click=lambda: setattr(st.session_state, 'current_chat_id', 
                                        datetime.now().strftime("%Y%m%d_%H%M%S")))
        
        st.markdown("### Previous Chats")
        for chat_id, chat_data in st.session_state.chats.items():
            if st.button(f"📝 {chat_data['title'][:20]}...", key=chat_id):
                st.session_state.current_chat_id = chat_id

    with col2:
        # Document Upload
        with st.expander("📁 Upload Documents"):
            uploaded_files = st.file_uploader(
                "Add documents to the knowledge base",
                accept_multiple_files=True,
                type=['pdf', 'docx', 'txt', 'xml', 'json', 'aird', 'capella']
            )
            
            if uploaded_files and st.button("Process Documents"):
                with st.spinner("Processing documents..."):
                    temp_paths = []
                    for uploaded_file in uploaded_files:
                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        temp_paths.append(temp_path)
                    
                    results = st.session_state.rag_system.add_documents(temp_paths)
                    
                    for temp_path in temp_paths:
                        os.remove(temp_path)
                    
                    st.success(f"Processed {results['processed']} files")
                    st.info(f"Added {results['chunks_added']} chunks to database")
                    
                    if results['errors']:
                        st.error("Errors encountered:")
                        for error in results['errors']:
                            st.write(f"- {error}")

        # Diagram Generation
        with st.expander("📊 Generate MBSE Diagram"):
            st.markdown("""
            Create a lightweight Capella diagram using natural language description.
            Choose the diagram type and describe what you want to create.
            """)
            
            diagram_type = st.selectbox(
                "Diagram Type",
                [dt.value for dt in DiagramType],
                key="diagram_type"
            )
            
            diagram_description = st.text_area(
                "Describe your diagram",
                placeholder="Example: Create a system with two components connected by an interface",
                key="diagram_description"
            )
            
            if st.button("Generate Diagram"):
                if diagram_description:
                    with st.spinner("Generating diagram..."):
                        # Convert string value back to enum
                        selected_type = next(dt for dt in DiagramType if dt.value == diagram_type)
                        diagram = st.session_state.diagram_generator.generate_diagram(
                            diagram_description, selected_type
                        )
                        # Save diagram to temp file and display
                        diagram_path = "temp_diagram"
                        diagram.render(diagram_path, format="png", cleanup=True)
                        st.image(f"{diagram_path}.png")
                        # Cleanup
                        os.remove(f"{diagram_path}.png")
                else:
                    st.warning("Please provide a description for your diagram.")

        # Chat Interface
        if st.session_state.current_chat_id:
            if st.session_state.current_chat_id not in st.session_state.chats:
                st.session_state.chats[st.session_state.current_chat_id] = {
                    "title": "New Chat",
                    "messages": []
                }
            
            current_chat = st.session_state.chats[st.session_state.current_chat_id]
            
            # Display chat messages
            for message in current_chat["messages"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "context" in message and message["role"] == "assistant":
                        with st.expander("View Context Sources"):
                            for i, doc in enumerate(message["context"]):
                                st.write(f"**Source {i+1}:** {doc['metadata'].get('source', 'Unknown')}")
                                st.write(f"**Content Preview:** {doc['content'][:200]}...")
                                st.divider()
            
            # Chat input
            if prompt := st.chat_input("Ask about your MBSE models..."):
                # Update chat title if it's the first message
                if not current_chat["messages"]:
                    current_chat["title"] = prompt[:50]
                
                # Add user message
                current_chat["messages"].append({"role": "user", "content": prompt})
                
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing..."):
                        response, context_docs = st.session_state.rag_system.chat(prompt)
                    
                    st.markdown(response)
                    
                    with st.expander("View Context Sources"):
                        for i, doc in enumerate(context_docs):
                            st.write(f"**Source {i+1}:** {doc['metadata'].get('source', 'Unknown')}")
                            st.write(f"**Content Preview:** {doc['content'][:200]}...")
                            st.divider()
                
                # Add assistant response
                current_chat["messages"].append({
                    "role": "assistant",
                    "content": response,
                    "context": context_docs
                })
                
                # Save chats
                save_chats(st.session_state.chats)
        else:
            st.info("👈 Create a new chat or select an existing one to start")

    with col3:
        with st.expander("⚙️ Settings"):
            st.selectbox("Model", ["gemma:7b", "llama2:7b", "mistral:7b"], key="model")
            st.slider("Context Length", 1, 10, 5, key="context_length")
            st.selectbox(
                "MBSE Context",
                ["None", "operational", "system", "logical", "physical", "verification", "traceability"],
                key="mbse_context"
            )

if __name__ == "__main__":
    main()