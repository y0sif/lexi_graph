"""
LexiGraph Gradio Web App
Transform lectures into visual knowledge graphs
"""

import gradio as gr
import os
import time
from core.pipeline import pipeline, EXAMPLE_LECTURE
from core.utils import (
    compile_dot_to_png, 
    generate_unique_filename, 
    validate_input_text,
    cleanup_old_files
)

# Global state for storing results
current_results = {
    "summary": "",
    "graph_path": "",
    "processing": False
}

def process_lecture(lecture_text, progress=gr.Progress()):
    """
    Process lecture text and generate knowledge graph
    
    Args:
        lecture_text (str): Input lecture content
        progress: Gradio progress tracker
    
    Returns:
        tuple: (status_message, graph_image, summary_text, download_file)
    """
    global current_results
    
    # Reset results
    current_results = {"summary": "", "graph_path": "", "processing": True}
    
    # Input validation
    if not lecture_text or not lecture_text.strip():
        return (
            "❌ **Error:** Please enter some lecture content to process.",
            None,
            "",
            None
        )
    
    is_valid, error_message = validate_input_text(lecture_text)
    if not is_valid:
        return (
            f"❌ **Input Error:** {error_message}",
            None,
            "",
            None
        )
    
    try:
        # Clean up old files
        cleanup_old_files()
        
        # Progress tracking with Gradio
        progress(0.1, desc="🔍 Validating content type...")
        
        def progress_callback(stage, message):
            if stage == "validating":
                progress(0.2, desc="🔍 Validation agent checking content...")
            elif stage == "analyzing":
                progress(0.5, desc="📝 Summarization agent analyzing content...")
            elif stage == "generating":
                progress(0.8, desc="🎨 Visualization agent creating graph...")
        
        # Process the lecture through the pipeline
        summary, dot_code = pipeline(lecture_text, progress_callback)
        
        # Check if processing failed
        if dot_code is None:
            current_results["processing"] = False
            
            # Handle different types of errors
            if "Invalid content type detected" in summary:
                error_msg = f"❌ **Content Validation Failed:** {summary}\n\n💡 **Tip:** Please provide educational content such as:\n- Academic lectures or presentations\n- Tutorial or course materials\n- Technical documentation\n- Informational articles with learning value"
            elif "Connection refused" in summary or "API" in summary:
                error_msg = f"❌ **Connection Error:** Check your Anthropic API key in your .env file\n\nError details: {summary}"
            else:
                error_msg = f"❌ **Processing Error:** {summary}"
            
            return (error_msg, None, "", None)
        
        progress(0.9, desc="🖼️ Rendering visual graph...")
        
        # Generate unique filename and compile to PNG
        output_filename = generate_unique_filename()
        graph_path = compile_dot_to_png(dot_code, output_filename)
        
        if graph_path and os.path.exists(graph_path):
            # Update global results
            current_results["summary"] = summary
            current_results["graph_path"] = graph_path
            current_results["processing"] = False
            
            progress(1.0, desc="✅ Knowledge graph ready!")
            
            success_msg = "🎉 **Success!** Your knowledge graph has been generated successfully!"
            
            return (
                success_msg,
                graph_path,  # This will display the image
                summary,     # This will show in the summary textbox
                graph_path   # This will be available for download
            )
        else:
            current_results["processing"] = False
            return (
                "❌ **Rendering Error:** Failed to render graph - Please contact support",
                None,
                "",
                None
            )
            
    except Exception as e:
        current_results["processing"] = False
        return (
            f"❌ **Unexpected Error:** {str(e)}",
            None,
            "",
            None
        )

def load_example():
    """Load example lecture content"""
    return EXAMPLE_LECTURE

def clear_all():
    """Clear all inputs and outputs"""
    global current_results
    current_results = {"summary": "", "graph_path": "", "processing": False}
    return "", "", None, "", None

# Custom CSS for better styling
custom_css = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #000000 !important;
}

.gradio-container * {
    color: #000000 !important;
}

.gradio-container label {
    color: #000000 !important;
    font-weight: 500;
}

.gradio-container p, .gradio-container div, .gradio-container span {
    color: #000000 !important;
}

.gradio-container textarea, .gradio-container input {
    color: #000000 !important;
    background-color: #ffffff !important;
}

.main-header {
    text-align: center;
    color: #1f77b4 !important;
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    color: #333333 !important;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}

.info-box {
    background: #e7f3ff;
    border: 1px solid #bee5eb;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    color: #000000 !important;
}

.success-box {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    color: #000000 !important;
}

.error-box {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    color: #000000 !important;
}

/* Ensure button text is readable */
.gradio-container button {
    color: #ffffff !important;
}

.gradio-container button[data-testid="primary-button"] {
    background-color: #007bff !important;
    color: #ffffff !important;
}

.gradio-container button[data-testid="secondary-button"] {
    background-color: #6c757d !important;
    color: #ffffff !important;
}

/* Fix any specific text areas or inputs */
.gradio-container .prose {
    color: #000000 !important;
}

.gradio-container .prose h1, 
.gradio-container .prose h2, 
.gradio-container .prose h3, 
.gradio-container .prose h4, 
.gradio-container .prose h5, 
.gradio-container .prose h6 {
    color: #000000 !important;
}

.gradio-container .prose p {
    color: #000000 !important;
}

.gradio-container .prose ul li {
    color: #000000 !important;
}
"""

# Create the Gradio interface
def create_interface():
    with gr.Blocks(css=custom_css, title="LexiGraph - Lecture to Knowledge Graph", theme=gr.themes.Soft()) as app:
        
        # Header
        gr.HTML("""
            <div class="main-header">🔗 LexiGraph</div>
            <div class="subtitle">Transform lectures into visual knowledge graphs</div>
        """)
        
        # API Key info
        gr.HTML("""
            <div class="info-box">
                ℹ️ <strong>API Configuration:</strong> Using Anthropic API key from environment file (.env)
            </div>
        """)
        
        # Main interface
        with gr.Row():
            with gr.Column(scale=3):
                lecture_input = gr.Textbox(
                    label="📝 Enter Your Lecture Content",
                    placeholder="Enter your lecture notes, slides, or any educational content...",
                    lines=12,
                    max_lines=20
                )
                
                with gr.Row():
                    generate_btn = gr.Button("🚀 Generate Knowledge Graph", variant="primary", scale=2)
                    example_btn = gr.Button("📚 Try Example Lecture", variant="secondary", scale=1)
                    clear_btn = gr.Button("🧹 Clear All", variant="stop", scale=1)
            
            with gr.Column(scale=1):
                gr.HTML("""
                    <div style="padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                        <h4>🤖 AI Agents</h4>
                        <p><strong>Three specialized agents:</strong></p>
                        <ul>
                            <li>🔍 <strong>Validation Agent</strong> - Content type checking</li>
                            <li>📝 <strong>Summarization Agent</strong> - Structure analysis</li>
                            <li>🎨 <strong>Visualization Agent</strong> - Graph generation</li>
                        </ul>
                        
                        <h4>💡 Tips</h4>
                        <ul>
                            <li>Use clear, structured content</li>
                            <li>Include main topics and subtopics</li>
                            <li>The longer the content, the richer the graph</li>
                        </ul>
                        
                        <h4>🛠️ Requirements</h4>
                        <ul>
                            <li><strong>Anthropic API</strong> key in .env file</li>
                            <li><strong>Model:</strong> claude-3-5-haiku-20241022</li>
                            <li><strong>Internet connection</strong> for API access</li>
                        </ul>
                    </div>
                """)
        
        # Results section
        gr.HTML("<hr>")
        
        status_output = gr.HTML(label="Status")
        
        with gr.Row():
            with gr.Column(scale=2):
                graph_output = gr.Image(
                    label="🎨 Generated Knowledge Graph",
                    show_label=True,
                    show_download_button=True,
                    container=True
                )
            
            with gr.Column(scale=1):
                summary_output = gr.Textbox(
                    label="📋 Generated Summary",
                    lines=10,
                    max_lines=15,
                    show_copy_button=True
                )
        
        # Download section
        download_file = gr.File(
            label="⬇️ Download Knowledge Graph",
            visible=True
        )
        
        # Event handlers
        generate_btn.click(
            fn=process_lecture,
            inputs=[lecture_input],
            outputs=[status_output, graph_output, summary_output, download_file],
            show_progress=True
        )
        
        example_btn.click(
            fn=load_example,
            outputs=[lecture_input]
        )
        
        clear_btn.click(
            fn=clear_all,
            outputs=[lecture_input, summary_output, graph_output, status_output, download_file]
        )
        
        # Footer with additional information
        gr.HTML("""
            <div style="margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                <h4>ℹ️ About LexiGraph</h4>
                <p><strong>LexiGraph</strong> transforms educational content into visual knowledge graphs using AI.</p>
                
                <p><strong>How it works:</strong></p>
                <p>🔍 Validates content type → 📝 Analyzes and structures content → 🎨 Generates visual diagrams → 🖼️ Renders beautiful graphs</p>
                
                <p><strong>Configuration:</strong> Add <code>ANTHROPIC_API_KEY=your_key_here</code> to your .env file</p>
                <p><a href="https://console.anthropic.com/" target="_blank">Get your API key from Anthropic Console</a></p>
            </div>
        """)
    
    return app

def main():
    """Main function to launch the Gradio app"""
    app = create_interface()
    
    # Launch the app
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )

if __name__ == "__main__":
    main()
