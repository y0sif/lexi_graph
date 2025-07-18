"""
Core pipeline functions for LexiGraph
Handles LLM processing and knowledge graph generation
"""

import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

def clean_deepseek_output(text: str) -> str:
    """
    Clean DeepSeek model output by removing thinking tags and extracting actual content
    
    Args:
        text (str): Raw output from DeepSeek model
    
    Returns:
        str: Cleaned output without thinking tags
    """
    # Remove <think> tags and content between them
    import re
    
    # Pattern to match <think>...</think> blocks (including multiline)
    think_pattern = r'<think>.*?</think>'
    cleaned_text = re.sub(think_pattern, '', text, flags=re.DOTALL)
    
    # Clean up extra whitespace and newlines
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

def create_llm():
    """Create and configure the LLM instance"""
    return ChatOllama(
        model="deepseek-r1:1.5b",
        temperature=0.1,
        num_ctx=8184,  # Context window
        base_url="http://localhost:11434",  # Default Ollama URL
    )

def create_prompts():
    """Create prompt templates for summarization and DOT generation"""
    
    summarizer_prompt = ChatPromptTemplate.from_template("""I want you to generate a detailed, hierarchical summary of a topic I provide, using the exact format described below. Your output should follow these formatting and content guidelines:

Use a hierarchical structure
Begin with the main topic, then move to subtopics, and then to sub-subtopics as needed. Each level should be clearly indented using this pattern:

Main Topic:
- Subtopic
-- Sub-subtopic
--- Detail or explanation
Use indentation and hyphens to express structure
Do not use prose or paragraphs. The entire output should be structured as an indented bullet-point list, making it easy to scan and review.

Provide definitions and explanations at each level
Each topic or algorithm must include a brief, clear description. If relevant, include:

What it does

Where or when it is used

A simple real-world example

Important strengths, weaknesses, or notes

Cover both broad and detailed information
For example, if the topic includes "Supervised Learning," list common algorithms under it, and for each algorithm, include further sub-points explaining its function and use cases.

Avoid unnecessary repetition or filler
Keep the summary concise but complete. Focus on clarity, logical organization, and informativeness.

Use this format as a style guide:

Artificial Intelligence (AI):
- Definition: Machines simulating human-like intelligence (e.g., learning, problem-solving, perception)
- Includes:
-- Machine Learning (ML)
-- Expert Systems
-- Natural Language Processing (NLP)
-- Robotics

Machine Learning (ML):
- Definition: Algorithms that learn patterns from data and make decisions with minimal human intervention
- Types:
-- Supervised Learning
--- Data: Labeled (input-output pairs)
--- Goal: Learn a function to predict outputs from inputs
--- Examples: Spam detection, price prediction
--- Common Algorithms:
---- Linear Regression
----- Predicts a continuous output from linear input relationships
----- Example: Predicting house prices from area and number of rooms
----- Simple, fast, and interpretable

Goal:
Produce a structured, study-ready summary. It should read like a clear and comprehensive cheat sheet or lecture outline on the topic.

Lecture content: {lecture}

Return ONLY the hierarchical summary without any explanations or additional text.""")

    dot_prompt = ChatPromptTemplate.from_template("""I want you to generate a Graphviz DOT file that visually represents a hierarchical summary of a topic. The input is a structured summary written in the following indentation style:

Main Topic:
- Subtopic
-- Sub-subtopic
--- Detail
Your output should follow these formatting and structural guidelines:

Use the DOT language syntax
Output valid Graphviz DOT code that can be rendered using tools like dot, xdot, or online Graphviz editors.

Graph orientation
Set the graph direction to left-to-right using rankdir=LR.

Nodes
Each item from the hierarchy (main topic, subtopics, details) should be represented as a separate node. Use shape=box and a simple lightgray color fill style for clarity.

Edges
Connect nodes based on their parent-child relationships, following the hierarchy. The edges should represent the "is part of" or "belongs to" relationship.

Node labels
Use the actual text from the summary as node labels. For multiline labels (e.g., descriptions or examples), use \n to format them properly within the node.

Hierarchy traversal
Preserve the hierarchy depth by linking each child node to its immediate parent. Do not skip levels, even if some levels are just categorical.

Example style
Your DOT code should look similar to this:

digraph TopicSummary {{
    rankdir=LR;
    node [shape=box, style=filled, color=lightgray];

    AI [label="Artificial Intelligence (AI)"];
    ML [label="Machine Learning (ML)"];
    AI -> ML;

    Supervised [label="Supervised Learning"];
    ML -> Supervised;

    LinearRegression [label="Linear Regression\nPredicts continuous values"];
    Supervised -> LinearRegression;
}} 
Goal:
Produce a clean, readable DOT file that accurately reflects the logical structure of the input summary. The graph should help someone visually understand the hierarchical relationships between topics, methods, and concepts in AI.

Hierarchical summary: {summary}

Return ONLY the DOT code without any explanations, additional text, or any ` used for annotating code, so don't put the code inside markdown syntax.""")
    
    return summarizer_prompt, dot_prompt

def pipeline(input_text: str, progress_callback=None):
    """
    Main pipeline function that processes lecture text into knowledge graph
    
    Args:
        input_text (str): The lecture content to process
        progress_callback (callable): Optional callback function for progress updates
    
    Returns:
        tuple: (summary, dot_code) or (error_message, None) on failure
    """
    try:
        # Create LLM and prompts
        llm = create_llm()
        summarizer_prompt, dot_prompt = create_prompts()
        
        # Create chains
        summarizer_chain = summarizer_prompt | llm
        dot_chain = dot_prompt | llm
        
        # Step 1: Generate summary
        if progress_callback:
            progress_callback("analyzing", "🔍 Analyzing lecture content...")
        
        summary_raw = summarizer_chain.invoke({"lecture": input_text}).content
        summary = clean_deepseek_output(summary_raw)
        
        # Step 2: Generate DOT code
        if progress_callback:
            progress_callback("generating", "🎨 Generating knowledge diagram...")
        
        dot_code_raw = dot_chain.invoke({"summary": summary}).content
        dot_code = clean_deepseek_output(dot_code_raw)
        
        return summary, dot_code
        
    except Exception as e:
        error_msg = f"Error during processing: {e}"
        print(error_msg)
        return error_msg, None

# Example lecture content for the web app
EXAMPLE_LECTURE = """Today we're going to talk about something fundamental in physics and chemistry: The States of Matter. At its core, matter is anything that has mass and occupies space. All matter exists in different forms known as states or phases.

1. Classical States of Matter
There are three primary states we encounter in everyday life:

🧊 Solid
Shape & Volume: Fixed shape and volume.

Particle Behavior: Particles are tightly packed in a regular pattern and vibrate in place.

Example: Ice, metal, wood.

💧 Liquid
Shape & Volume: Fixed volume but takes the shape of its container.

Particle Behavior: Particles are close together but can move/slide past each other.

Example: Water, oil, alcohol.

🌬️ Gas
Shape & Volume: No fixed shape or volume; expands to fill the container.

Particle Behavior: Particles are far apart and move freely at high speeds.

Example: Air, oxygen, carbon dioxide.

2. Other (Less Common) States
Beyond the classical states, scientists recognize other exotic states, especially in advanced physics:

⚡ Plasma
Found in stars, lightning, and neon signs.

Composed of ionized gas — atoms are split into electrons and ions.

Behaves differently due to electrical conductivity and response to magnetic fields.

🧪 Bose–Einstein Condensate (BEC)
Discovered in 1995.

Occurs at temperatures near absolute zero.

Particles lose individual identity and behave as one "super-particle."

Shows quantum effects on a macroscopic scale.

3. Transitions Between States
Matter can change from one state to another through phase changes, depending on temperature and pressure:

Melting (solid → liquid)

Freezing (liquid → solid)

Evaporation/Boiling (liquid → gas)

Condensation (gas → liquid)

Sublimation (solid → gas)

Deposition (gas → solid)."""
