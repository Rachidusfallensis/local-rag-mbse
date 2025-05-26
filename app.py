import streamlit as st
import os
from pathlib import Path
from rag_system import LocalRAGSystem
import config

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide"
)

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

def main():
    st.title(" AI-powered assistant for Model-Based Systems Engineering with Arcadia methodology")
    
    # Add info about Arcadia methodology
    with st.expander("ℹ️ About Arcadia Methodology"):
        st.markdown("""
        **Arcadia** is a model-based engineering method for systems architecting. It provides:
        
        - **Operational Analysis**: Understanding stakeholder needs and operational context
        - **System Analysis**: Defining system requirements and functions  
        - **Logical Architecture**: Designing solution components and interfaces
        - **Physical Architecture**: Implementing and deploying the solution
        
        This assistant helps you work with Capella models following the Arcadia methodology.
        """)
    
    # Initialize system
    rag_system = init_rag_system()
    
    # Sidebar for document management and references
    with st.sidebar:
        st.header("📁 Document Management")
        
        # Collection statistics
        stats = rag_system.get_collection_stats()
        st.metric("Documents in Database", stats["total_documents"])
        
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Choose files to add to the knowledge base",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'xml', 'json', 'aird', 'capella']
        )
        
        if uploaded_files:
            if st.button("Process Documents"):
                with st.spinner("Processing documents..."):
                    # Save uploaded files temporarily
                    temp_paths = []
                    for uploaded_file in uploaded_files:
                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        temp_paths.append(temp_path)
                    
                    # Process documents
                    results = rag_system.add_documents(temp_paths)
                    
                    # Clean up temporary files
                    for temp_path in temp_paths:
                        os.remove(temp_path)
                    
                    # Display results
                    st.success(f"Processed {results['processed']} files")
                    st.info(f"Added {results['chunks_added']} chunks to database")
                    
                    if results['errors']:
                        st.error("Errors encountered:")
                        for error in results['errors']:
                            st.write(f"- {error}")
        
        st.subheader("Settings")
        n_context = st.slider("Number of context documents", 1, 10, 5)
        
        available_models = ["gemma3:12b", "llama2:13b", "llama2:7b", "mistral:7b"]
        selected_model = st.selectbox("Select Model", available_models)
        
        # MBSE Analysis Context
        st.subheader("🎯 MBSE Analysis Context")
        context_type = st.selectbox(
            "Select analysis perspective",
            ["None", "operational", "system", "logical", "physical", "verification", "traceability"],
            help="Choose an MBSE perspective to enhance your queries"
        )
        
        # Display Arcadia references
        display_arcadia_references()
    
    # Main chat interface
    st.header("💬 Chat with your MBSE Assistant")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "context" in message and message["role"] == "assistant":
                with st.expander("View Context Sources"):
                    for i, doc in enumerate(message["context"]):
                        st.write(f"**Source {i+1}:** {doc['metadata'].get('source', 'Unknown')}")
                        st.write(f"**Type:** {doc['metadata'].get('type', 'Unknown')}")
                        if 'distance' in doc and doc['distance']:
                            st.write(f"**Relevance Score:** {1 - doc['distance']:.3f}")
                        st.write(f"**Content Preview:** {doc['content'][:200]}...")
                        st.divider()
    
    # Chat input
    if prompt := st.chat_input("Ask about your MBSE models and documentation..."):
        # Enhance prompt with MBSE context if selected
        context_selection = context_type if context_type != "None" else None
        enhanced_prompt = get_enhanced_prompt(prompt, context_selection)
        
        # Add user message to chat history (show original prompt to user)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response using enhanced prompt
        with st.chat_message("assistant"):
            with st.spinner("Analyzing from MBSE perspective..."):
                response, context_docs = rag_system.chat(enhanced_prompt, n_context)
            
            st.markdown(response)
            
            # Show context sources
            with st.expander("View Context Sources"):
                for i, doc in enumerate(context_docs):
                    st.write(f"**Source {i+1}:** {doc['metadata'].get('source', 'Unknown')}")
                    st.write(f"**Type:** {doc['metadata'].get('type', 'Unknown')}")
                    if 'distance' in doc and doc['distance']:
                        st.write(f"**Relevance Score:** {1 - doc['distance']:.3f}")
                    st.write(f"**Content Preview:** {doc['content'][:200]}...")
                    st.divider()
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "context": context_docs
        })
    
    # Enhanced MBSE sample queries organized by Arcadia phases
    st.header("🔍 Sample MBSE Queries by Arcadia Phase")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎭 Operational Analysis")
        if st.button("Stakeholder Analysis"):
            st.session_state.sample_query = ("Who are the key stakeholders and what are their needs?", "operational")
        
        if st.button("Operational Activities"):
            st.session_state.sample_query = ("What are the main operational activities and scenarios?", "operational")
        
        st.subheader("⚙️ System Analysis") 
        if st.button("System Functions"):
            st.session_state.sample_query = ("What are the key system functions and their relationships?", "system")
        
        if st.button("System Requirements"):
            st.session_state.sample_query = ("What are the functional and non-functional requirements?", "system")
    
    with col2:
        st.subheader("🏗️ Logical Architecture")
        if st.button("Logical Components"):
            st.session_state.sample_query = ("What are the logical components and their interfaces?", "logical")
        
        if st.button("Behavioral Analysis"):
            st.session_state.sample_query = ("Describe the key behavioral scenarios and interactions", "logical")
        
        st.subheader("🔧 Physical Architecture")
        if st.button("Physical Implementation"):
            st.session_state.sample_query = ("How is the system physically implemented and deployed?", "physical")
        
        if st.button("V&V Approach"):
            st.session_state.sample_query = ("What is the verification and validation approach?", "verification")
    
    # Handle sample queries
    if "sample_query" in st.session_state:
        # Get the sample query and context
        query_data = st.session_state.sample_query
        if isinstance(query_data, tuple):
            prompt, query_context = query_data
        else:
            prompt = query_data
            query_context = None
        
        del st.session_state.sample_query
        
        # Enhance prompt with context
        enhanced_prompt = get_enhanced_prompt(prompt, query_context)
        
        # Add to messages and process
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing from MBSE perspective..."):
                response, context_docs = rag_system.chat(enhanced_prompt, n_context)
            st.markdown(response)
            
            # Show context sources
            with st.expander("View Context Sources"):
                for i, doc in enumerate(context_docs):
                    st.write(f"**Source {i+1}:** {doc['metadata'].get('source', 'Unknown')}")
                    st.write(f"**Type:** {doc['metadata'].get('type', 'Unknown')}")
                    if 'distance' in doc and doc['distance']:
                        st.write(f"**Relevance Score:** {1 - doc['distance']:.3f}")
                    st.write(f"**Content Preview:** {doc['content'][:200]}...")
                    st.divider()
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "context": context_docs
        })
        st.rerun()

if __name__ == "__main__":
    main()