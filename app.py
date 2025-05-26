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

# Custom CSS for better UI and scrolling behavior
st.markdown("""
<style>
    .chat-container {
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        max-height: 600px;
        overflow-y: auto;
    }
    .user-message {
        background-color: #e6f3ff;
        text-align: right;
        padding: 10px;
        margin: 5px 0;
        border-radius: 10px;
    }
    .assistant-message {
        background-color: #f0f2f6;
        padding: 10px;
        margin: 5px 0;
        border-radius: 10px;
    }
    .chat-input {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 10px;
        border-top: 1px solid #ddd;
    }
    .chat-messages {
        overflow-y: auto;
        max-height: calc(100vh - 200px);
        padding-bottom: 100px;
    }
    .stApp {
        height: 100vh;
    }
    .diagram-container {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .diagram-explanation {
        background: #f8f9fa;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 10px 10px 0;
    }
    
    /* Make diagram section responsive */
    .diagram-section {
        transition: all 0.3s ease;
        min-height: 200px;
    }
    
    .diagram-section.expanded {
        min-height: 600px;
    }
    
    /* Improve image display */
    .diagram-image {
        max-width: 100%;
        height: auto;
        margin: 10px 0;
    }
</style>

<script>
    // Function to scroll to bottom of chat
    function scrollToBottom() {
        const messages = document.querySelector('.chat-messages');
        if (messages) {
            messages.scrollTop = messages.scrollHeight;
        }
    }
    
    // Call scrollToBottom when new messages are added
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                scrollToBottom();
            }
        });
    });
    
    // Start observing the chat messages container
    window.addEventListener('load', () => {
        const messages = document.querySelector('.chat-messages');
        if (messages) {
            observer.observe(messages, { childList: true, subtree: true });
            scrollToBottom();
        }
    });
</script>
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
        st.session_state.diagram_generator = CapellaDiagramGenerator(st.session_state.rag_system)

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
        diagram_section = st.container()
        with diagram_section:
            st.markdown('<div class="diagram-section">', unsafe_allow_html=True)
            
            st.subheader("📊 Generate MBSE Diagram")
            st.markdown("""
            Create a lightweight overview diagram based on your project documents.
            The system will analyze your documents and suggest the most important elements
            to include in an initial draft diagram.
            """)
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                diagram_type = st.selectbox(
                    "Diagram Type",
                    [dt.value for dt in DiagramType],
                    key="diagram_type"
                )
                
                max_elements = st.slider(
                    "Maximum Elements",
                    min_value=3,
                    max_value=15,
                    value=7,
                    help="Maximum number of elements to include in the overview diagram"
                )
            
            with col_right:
                st.markdown("""
                **Diagram Focus Areas:**
                - High-level overview
                - Key elements and relationships
                - Most frequently mentioned components
                - Important interfaces and connections
                """)
            
            diagram_description = st.text_area(
                "Describe what to include in the diagram",
                placeholder="Example: Show the main operational activities related to user authentication and system startup",
                key="diagram_description"
            )
            
            generate_col1, generate_col2 = st.columns([1, 3])
            with generate_col1:
                generate_button = st.button("Generate Overview Diagram")
            
            if generate_button:
                if diagram_description:
                    with st.spinner("Analyzing documents and generating overview diagram..."):
                        try:
                            # Convert string value back to enum
                            selected_type = next(dt for dt in DiagramType if dt.value == diagram_type)
                            diagram = st.session_state.diagram_generator.generate_diagram(
                                diagram_description, 
                                selected_type,
                                max_elements=max_elements
                            )
                            
                            # Create a container for the diagram and its explanation
                            st.markdown('<div class="diagram-container">', unsafe_allow_html=True)
                            
                            # Save and display diagram
                            diagram_path = "temp_diagram"
                            diagram.render(diagram_path, format="png", cleanup=True)
                            
                            # Display diagram with proper styling
                            st.markdown('<div class="diagram-image">', unsafe_allow_html=True)
                            st.image(f"{diagram_path}.png", use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Show explanation without using expander
                            st.markdown('<div class="diagram-explanation">', unsafe_allow_html=True)
                            st.markdown("""
                            **Diagram Overview:**
                            - The most important elements based on document analysis
                            - Elements grouped by type (activities, components, etc.)
                            - Key relationships between elements
                            - Tooltips with additional details (hover over elements)
                            """)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Cleanup
                            os.remove(f"{diagram_path}.png")
                            
                        except Exception as e:
                            st.error(f"Error generating diagram: {str(e)}")
                            if "Graphviz executables" in str(e):
                                st.warning("""
                                Graphviz is not installed. Please install it:
                                - macOS: `brew install graphviz`
                                - Ubuntu: `sudo apt-get install graphviz`
                                - Windows: `choco install graphviz`
                                """)
                else:
                    st.warning("Please provide a description for your diagram.")
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Chat Interface
        if st.session_state.current_chat_id:
            if st.session_state.current_chat_id not in st.session_state.chats:
                st.session_state.chats[st.session_state.current_chat_id] = {
                    "title": "New Chat",
                    "messages": []
                }
            
            current_chat = st.session_state.chats[st.session_state.current_chat_id]
            
            # Create a container for chat messages with auto-scroll
            chat_container = st.container()
            with chat_container:
                st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
                
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
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Chat input at the bottom
            st.markdown('<div class="chat-input">', unsafe_allow_html=True)
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
            st.markdown('</div>', unsafe_allow_html=True)
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