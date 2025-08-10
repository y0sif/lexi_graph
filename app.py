"""
LexiGraph Streamlit Web App
Transform lectures into visual knowledge graphs
"""

import streamlit as st
import os
import time
from core.pipeline import pipeline, EXAMPLE_LECTURE
from core.utils import (
    compile_dot_to_png, 
    generate_unique_filename, 
    validate_input_text,
    cleanup_old_files
)

# Progress messages
PROGRESS_MESSAGES = {
    "validating": "🔍 Validating content type...",
    "analyzing": "� Analyzing lecture content...",
    "generating": "🎨 Generating knowledge diagram...",
    "rendering": "🖼️ Rendering visual graph...",
    "complete": "✅ Knowledge graph ready!"
}

# Error messages
ERROR_MESSAGES = {
    "invalid_content": "❌ Content validation failed - Please provide educational content",
    "connection": "❌ Connection error - Check your Anthropic API key",
    "analysis": "❌ Failed to analyze content - Please check your text",
    "generation": "❌ Failed to generate diagram - Please try again",
    "rendering": "❌ Failed to render graph - Please contact support"
}

def init_session_state():
    """Initialize session state variables"""
    if 'graph_generated' not in st.session_state:
        st.session_state.graph_generated = False
    if 'current_summary' not in st.session_state:
        st.session_state.current_summary = ""
    if 'graph_path' not in st.session_state:
        st.session_state.graph_path = ""
    if 'lecture_text' not in st.session_state:
        st.session_state.lecture_text = ""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""

def on_text_change():
    """Callback for when text input changes"""
    # This will trigger a rerun automatically when text changes
    pass

def progress_callback(stage, message):
    """Callback function for progress updates"""
    st.session_state.current_stage = stage
    st.session_state.current_message = message

def clear_results():
    """Clear all results and reset session state"""
    st.session_state.graph_generated = False
    st.session_state.current_summary = ""
    st.session_state.graph_path = ""
    st.session_state.lecture_text = ""
    # Don't clear API key when clearing results
    st.rerun()

def main():
    # Page configuration
    st.set_page_config(
        page_title="LexiGraph - Lecture to Knowledge Graph",
        page_icon="🔗",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    init_session_state()
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 1.2rem;
    }
    .success-message {
        background: #d4edda;
        color: black;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-message {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header Section
    st.markdown('<div class="main-header">🔗 LexiGraph</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Transform lectures into visual knowledge graphs</div>', unsafe_allow_html=True)
    
    # API Key Section - COMMENTED OUT FOR NOW (using .env file)
    # st.markdown("### 🔑 Anthropic API Configuration")
    
    # # API Key input in main area with better styling
    # with st.container():
    #     api_key = st.text_input(
    #         "Enter your Anthropic API Key:",
    #         type="password",
    #         value=st.session_state.api_key,
    #         placeholder="sk-ant-...",
    #         help="Get your API key from https://console.anthropic.com/",
    #         key="api_input",
    #         on_change=lambda: setattr(st.session_state, 'api_key', st.session_state.api_input)
    #     )
        
    #     st.markdown("[Anthropic Console](https://console.anthropic.com/)")
        
    #     if st.button("🗑️ Clear Key", use_container_width=True):
    #         st.session_state.api_key = ""
    #         st.rerun()
    
    # For now, using API key from .env file only
    api_key = None  # Will use environment variable
    
    # Update session state
    st.session_state.api_key = api_key
    
    # API key status - commented out since we're using .env
    # if api_key and api_key.startswith("sk-ant-"):
    #     st.success("✅ API key configured successfully!")
    # elif api_key:
    #     st.warning("⚠️ API key should start with 'sk-ant-'")
    # else:
    #     st.info("ℹ️ Using API key from environment file (.env)")
    
    st.info("ℹ️ Using Anthropic API key from environment file (.env)")
    
    st.markdown("---")
    
    # Input Section
    st.markdown("### 📝 Enter Your Lecture Content")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        lecture_text = st.text_area(
            "Paste your lecture content here:",
            value=st.session_state.lecture_text,
            height=300,
            placeholder="Enter your lecture notes, slides, or any educational content...",
            key="lecture_input",
            on_change=on_text_change
        )
    
    with col2:
        st.markdown("##### Quick Actions")
        if st.button("📚 Try Example Lecture", type="secondary", use_container_width=True):
            st.session_state.lecture_text = EXAMPLE_LECTURE
            st.rerun()
        
        if st.button("🧹 Clear All", use_container_width=True):
            clear_results()
    
    # Update session state
    st.session_state.lecture_text = lecture_text
    
    # Action Section
    st.markdown("---")
    
    # Input validation (only check validity, don't show warning)
    is_valid, error_message = validate_input_text(lecture_text)
    generate_disabled = not is_valid  # Only check text validity now
    
    # Generate button with dynamic text based on input state
    button_text = "🚀 Generate Knowledge Graph"
    if not lecture_text or not lecture_text.strip():
        button_text = "✏️ Enter lecture content to generate graph"
    elif len(lecture_text.strip()) < 50:
        button_text = f"📝 Need at least {50 - len(lecture_text.strip())} more characters"
    
    # Generate button
    if st.button(
        button_text, 
        type="primary", 
        disabled=generate_disabled,
        use_container_width=True
    ):
        # Double-check validation when button is clicked            
        if not is_valid:
            st.error(f"**Input Error:** {error_message}")
            return
            
        # Clean up old files
        cleanup_old_files()
        
        # Progress tracking
        with st.status("Generating your knowledge graph...", expanded=True) as status:
            try:
                # Step 1: Validation
                status.update(label=PROGRESS_MESSAGES["validating"], state="running")
                time.sleep(0.5)  # Small delay for visual feedback
                
                # Step 2: Processing pipeline
                summary, dot_code = pipeline(lecture_text, progress_callback)
                
                # Check if validation failed or processing failed
                if dot_code is None:
                    status.update(label="❌ Processing failed", state="error")
                    
                    # Check if it's a validation error (contains validation error message)
                    if "Invalid content type detected" in summary:
                        st.error(f"**Content Validation Failed:** {summary}")
                        st.info("💡 **Tip:** Please provide educational content such as:\n"
                               "- Academic lectures or presentations\n"
                               "- Tutorial or course materials\n" 
                               "- Technical documentation\n"
                               "- Informational articles with learning value")
                    elif "Connection refused" in summary or "API" in summary:
                        st.error(ERROR_MESSAGES["connection"])
                        st.info("💡 **Quick Fix:** Check your Anthropic API key in your .env file")
                    else:
                        st.error(f"**Processing Error:** {summary}")
                    return
                
                status.update(label=PROGRESS_MESSAGES["generating"], state="running")
                time.sleep(0.5)
                
                # Step 3: Rendering
                status.update(label=PROGRESS_MESSAGES["rendering"], state="running")
                
                # Generate unique filename and compile to PNG
                output_filename = generate_unique_filename()
                graph_path = compile_dot_to_png(dot_code, output_filename)
                
                if graph_path:
                    # Update session state
                    st.session_state.graph_generated = True
                    st.session_state.current_summary = summary
                    st.session_state.graph_path = graph_path
                    
                    status.update(label=PROGRESS_MESSAGES["complete"], state="complete")
                else:
                    status.update(label="❌ Failed to render graph", state="error")
                    st.error(ERROR_MESSAGES["rendering"])
                
            except Exception as e:
                status.update(label="❌ Unexpected error occurred", state="error")
                st.error(f"**Unexpected Error:** {str(e)}")
    
    # Results Section
    if st.session_state.graph_generated and st.session_state.graph_path:
        st.markdown("---")
        st.markdown("### 🎉 Your Knowledge Graph is Ready!")
        
        # Display the generated image
        try:
            st.image(
                st.session_state.graph_path,
                caption="Generated Knowledge Graph",
                use_container_width=True
            )
            
            # Download section
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Download button
                if os.path.exists(st.session_state.graph_path):
                    with open(st.session_state.graph_path, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Knowledge Graph",
                            data=file.read(),
                            file_name=f"knowledge_graph_{int(time.time())}.png",
                            mime="image/png",
                            type="primary",
                            use_container_width=True
                        )

            # Optional: Show summary in expandable section
            with st.expander("📋 View Generated Summary (Optional)"):
                st.text(st.session_state.current_summary)
            
            # Success message
            st.markdown(
                '<div class="success-message">'
                '<strong>🎉 Success!</strong> Your knowledge graph has been generated successfully. '
                'You can download it using the button above.'
                '</div>',
                unsafe_allow_html=True
            )
            
        except Exception as e:
            st.error(f"Error displaying image: {e}")
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("### ℹ️ About LexiGraph")
        st.markdown("""
        **LexiGraph** transforms educational content into visual knowledge graphs using AI.
        
        **How it works:**
        1. 🔍 Validates content type
        2. 📝 Analyzes and structures content
        3. 🎨 Generates visual diagrams
        4. 🖼️ Renders beautiful graphs
        
        **Tips:**
        - Use clear, structured content
        - Include main topics and subtopics
        - The longer the content, the richer the graph
        """)
        
        st.markdown("### 🛠️ Requirements")
        st.markdown("""
        - **Anthropic API** key configured in .env file
        - **Model:** claude-3-5-haiku-20241022
        - **Internet connection** for API access
        
        **Getting Started:**
        1. Ensure your Anthropic API key is in the .env file
        2. Paste educational content below
        3. Generate your knowledge graph!
        """)
        
        st.markdown("### 🔧 Configuration")
        st.markdown("""
        **API Key Setup:**
        - Add `ANTHROPIC_API_KEY=your_key_here` to your .env file
        - Get your API key from [Anthropic Console](https://console.anthropic.com/)
        """)
        
        st.markdown("### 🤖 AI Agents")
        st.markdown("""
        **Three specialized agents:**
        1. 🔍 **Validation Agent** - Content type checking
        2. 📝 **Summarization Agent** - Structure analysis  
        3. 🎨 **Visualization Agent** - Graph generation
        """)
        
        if st.button("🔄 Refresh Page"):
            st.rerun()

if __name__ == "__main__":
    main()
