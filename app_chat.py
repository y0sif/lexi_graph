"""
LexiGraph Streamlit Web App - Chatbot Interface
Transform lectures into visual knowledge graphs with a chat-like UI
"""

import streamlit as st
import os
import time
import base64
from io import BytesIO
from datetime import datetime
from core.pipeline import pipeline, EXAMPLE_LECTURE
from core.utils import (
    compile_dot_to_png, 
    generate_unique_filename, 
    validate_input_text,
    cleanup_old_files
)

def init_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm LexiGraph 🔗. Send me your lecture content and I'll transform it into a beautiful knowledge graph!",
                "timestamp": datetime.now(),
                "type": "text"
            }
        ]
    if 'processing' not in st.session_state:
        st.session_state.processing = False

def get_file_download_link(file_path, filename):
    """Generate a download link for a file"""
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    b64 = base64.b64encode(bytes_data).decode()
    return f'data:image/png;base64,{b64}'

def add_user_message(content):
    """Add a user message to the chat"""
    st.session_state.messages.append({
        "role": "user", 
        "content": content,
        "timestamp": datetime.now(),
        "type": "text"
    })

def add_assistant_message(content, message_type="text", graph_path=None, summary=None):
    """Add an assistant message to the chat"""
    message = {
        "role": "assistant",
        "content": content,
        "timestamp": datetime.now(),
        "type": message_type
    }
    if graph_path:
        message["graph_path"] = graph_path
    if summary:
        message["summary"] = summary
    
    st.session_state.messages.append(message)

def display_message(message):
    """Display a single message in the chat"""
    is_user = message["role"] == "user"
    
    # Create columns for alignment
    if is_user:
        col1, col2 = st.columns([1, 4])
        with col2:
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: #007acc;
                    color: white;
                    padding: 15px;
                    border-radius: 18px 18px 5px 18px;
                    margin: 5px 0;
                    max-width: 80%;
                    margin-left: auto;
                    word-wrap: break-word;
                ">
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # Timestamp
                timestamp = message['timestamp'].strftime("%H:%M")
                st.markdown(f"""
                <div style="text-align: right; font-size: 0.8em; color: #666; margin-top: 2px;">
                    {timestamp}
                </div>
                """, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.container():
                if message["type"] == "graph":
                    # Graph message with image and controls
                    st.markdown(f"""
                    <div style="
                        background-color: #f1f1f1;
                        color: #333;
                        padding: 15px;
                        border-radius: 18px 18px 18px 5px;
                        margin: 5px 0;
                        max-width: 90%;
                    ">
                        <div style="margin-bottom: 10px;">
                            <strong>🎉 {message['content']}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display the graph
                    if "graph_path" in message and os.path.exists(message["graph_path"]):
                        st.image(message["graph_path"], use_column_width=True)
                        
                        # Action buttons
                        col_download, col_preview, col_summary = st.columns([1, 1, 1])
                        
                        with col_download:
                            with open(message["graph_path"], "rb") as file:
                                st.download_button(
                                    label="⬇️ Download",
                                    data=file.read(),
                                    file_name=f"knowledge_graph_{int(time.time())}.png",
                                    mime="image/png",
                                    key=f"download_{message['timestamp']}",
                                    use_container_width=True
                                )
                        
                        with col_preview:
                            if st.button("👁️ Preview", key=f"preview_{message['timestamp']}", use_container_width=True):
                                with st.expander("🖼️ Full Size Preview", expanded=True):
                                    st.image(message["graph_path"], use_column_width=True)
                        
                        with col_summary:
                            if "summary" in message and st.button("📋 Summary", key=f"summary_{message['timestamp']}", use_container_width=True):
                                with st.expander("📋 Generated Summary", expanded=True):
                                    st.text(message["summary"])
                else:
                    # Regular text message
                    st.markdown(f"""
                    <div style="
                        background-color: #f1f1f1;
                        color: #333;
                        padding: 15px;
                        border-radius: 18px 18px 18px 5px;
                        margin: 5px 0;
                        max-width: 80%;
                    ">
                        {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Timestamp
                timestamp = message['timestamp'].strftime("%H:%M")
                st.markdown(f"""
                <div style="text-align: left; font-size: 0.8em; color: #666; margin-top: 2px;">
                    🔗 LexiGraph • {timestamp}
                </div>
                """, unsafe_allow_html=True)

def display_typing_indicator():
    """Display a typing indicator"""
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
        <div style="
            background-color: #f1f1f1;
            color: #333;
            padding: 15px;
            border-radius: 18px 18px 18px 5px;
            margin: 5px 0;
            max-width: 80%;
        ">
            <div style="display: flex; align-items: center;">
                <div style="margin-right: 10px;">🔗 LexiGraph is generating your knowledge graph...</div>
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Page configuration
    st.set_page_config(
        page_title="LexiGraph Chat - Lecture to Knowledge Graph",
        page_icon="🔗",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    init_session_state()
    
    # Custom CSS for chatbot styling
    st.markdown("""
    <style>
    /* Fixed page layout */
    .main > div {
        padding-top: 0rem;
        height: 100vh;
        overflow: hidden;
    }
    
    .stApp {
        height: 100vh;
        overflow: hidden;
    }
    
    .chat-header {
        background: linear-gradient(90deg, #007acc, #005999);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 15px;
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    
    .chat-container {
        height: calc(100vh - 280px);
        overflow-y: auto;
        overflow-x: hidden;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #fafafa;
        margin-bottom: 15px;
        scrollbar-width: thin;
        scrollbar-color: #007acc #f1f1f1;
    }
    
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #007acc;
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #005999;
    }
    
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 15px 20px;
        border-top: 1px solid #ddd;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    
    .input-container .stTextArea {
        margin-bottom: 10px;
    }
    
    .typing-dots span {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #007acc;
        margin: 0 2px;
        animation: typing 1.4s infinite;
    }
    
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
    
    /* Message styling */
    .message-container {
        margin-bottom: 15px;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Adjust sidebar */
    .css-1d391kg {
        padding-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="chat-header">
        <h1 style="margin: 0; font-size: 1.8rem;">🔗 LexiGraph Chat</h1>
        <p style="margin: 0; opacity: 0.9;">Transform lectures into visual knowledge graphs</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat container with fixed height
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display all messages
    for i, message in enumerate(st.session_state.messages):
        st.markdown('<div class="message-container">', unsafe_allow_html=True)
        display_message(message)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Show typing indicator if processing
    if st.session_state.processing:
        st.markdown('<div class="message-container">', unsafe_allow_html=True)
        display_typing_indicator()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add some space for the fixed input
    st.markdown('<div style="height: 180px;"></div>', unsafe_allow_html=True)
    
    # Auto-scroll to bottom script
    st.markdown("""
    <script>
    function scrollToBottom() {
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    // Auto-scroll when page loads
    window.addEventListener('load', scrollToBottom);
    
    // Auto-scroll when content changes
    const observer = new MutationObserver(scrollToBottom);
    const targetNode = document.querySelector('.chat-container');
    if (targetNode) {
        observer.observe(targetNode, { childList: true, subtree: true });
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Input section (fixed at bottom)
    input_container = st.container()
    
    with input_container:
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        
        # Quick action buttons
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("📚 Example", use_container_width=True, disabled=st.session_state.processing):
                add_user_message("Here's an example lecture about AI and Machine Learning:")
                add_user_message(EXAMPLE_LECTURE)
                st.rerun()
        
        with col2:
            if st.button("🧹 Clear", use_container_width=True, disabled=st.session_state.processing):
                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": "Hi! I'm LexiGraph 🔗. Send me your lecture content and I'll transform it into a beautiful knowledge graph!",
                        "timestamp": datetime.now(),
                        "type": "text"
                    }
                ]
                st.rerun()
        
        # Text input with send button in same row
        col_input, col_send = st.columns([4, 1])
        
        with col_input:
            user_input = st.text_area(
                "Type your lecture content here...",
                height=80,
                placeholder="Paste your lecture notes, slides, or any educational content here...",
                disabled=st.session_state.processing,
                key="user_input",
                label_visibility="collapsed"
            )
        
        with col_send:
            st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)  # Align with text area
            send_button = st.button(
                "🚀 Send",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.processing or not user_input.strip()
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Process user input
    if send_button and user_input.strip() and not st.session_state.processing:
        # Validate input
        is_valid, error_message = validate_input_text(user_input)
        
        if not is_valid:
            add_assistant_message(f"❌ {error_message}")
            st.rerun()
        else:
            # Add user message
            add_user_message(user_input)
            
            # Set processing state
            st.session_state.processing = True
            
            # Process the lecture
            try:
                # Clean up old files
                cleanup_old_files()
                
                # Generate the knowledge graph
                summary, dot_code = pipeline(user_input)
                
                if dot_code is None:
                    add_assistant_message(f"❌ Sorry, I couldn't process your lecture. Error: {summary}")
                    st.session_state.processing = False
                    st.rerun()
                else:
                    # Generate unique filename and compile to PNG
                    output_filename = generate_unique_filename()
                    graph_path = compile_dot_to_png(dot_code, output_filename)
                    
                    if graph_path:
                        add_assistant_message(
                            "Your knowledge graph is ready!",
                            message_type="graph",
                            graph_path=graph_path,
                            summary=summary
                        )
                    else:
                        add_assistant_message("❌ Sorry, I couldn't render the graph. Please try again.")
                    
                    st.session_state.processing = False
                    
            except Exception as e:
                add_assistant_message(f"❌ Oops! Something went wrong: {str(e)}")
                st.session_state.processing = False
            
            # Clear input and rerun
            st.session_state.user_input = ""
            st.rerun()
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("### ℹ️ About LexiGraph")
        st.markdown("""
        **LexiGraph** transforms educational content into visual knowledge graphs using AI.
        
        **How it works:**
        1. 🔍 Analyzes your lecture content
        2. 📝 Creates structured summaries  
        3. 🎨 Generates visual diagrams
        4. 🖼️ Renders beautiful graphs
        
        **Tips:**
        - Use clear, structured content
        - Include main topics and subtopics
        - The longer the content, the richer the graph
        """)
        
        st.markdown("### 🛠️ Status")
        if st.session_state.processing:
            st.info("🔄 Processing your request...")
        else:
            st.success("✅ Ready to process lectures")
        
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")

if __name__ == "__main__":
    main()
