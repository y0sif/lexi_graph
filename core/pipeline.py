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

def create_llm():
    """Create and configure the LLM instance"""
    return ChatOllama(
        model="gemma3n:e2b",
        temperature=0.0,
        num_ctx=4096,  # Context window
        base_url="http://localhost:11434",  # Default Ollama URL
    )

def create_prompts():
    """Create prompt templates for summarization and DOT generation"""
    
    summarizer_prompt = ChatPromptTemplate.from_template("""Create a hierarchical summary of this lecture content: {lecture}

Format the summary as a tree structure using dashes (-) for each level. Maintain the original language of the content. Example format:

Main Topic:
-Subtopic 1
--Detail A
--Detail B
-Subtopic 2
--Detail C
--Detail D

try to make each subsection small and concise, but still informative.
                                                         
if you need to make a subsection of a subsection do it.

Return ONLY the hierarchical summary without any explanations or additional text.
                                                     
If it is already summarized in the way shown above, return it as is.""")

    dot_prompt = ChatPromptTemplate.from_template("""Given the following hierarchical summary of a lecture: {summary}

Create a digraph that represents the hierarchy. Use proper graphiz DOT syntax with directed edges (->) and include 'rankdir=LR' in the graph attributes. Make sure to preserve the language of the content and add appropriate styling for better visualization.

If the input given is not a summary, do not generate a DOT code for it.
                                              
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
        
        summary = summarizer_chain.invoke({"lecture": input_text}).content
        
        # Step 2: Generate DOT code
        if progress_callback:
            progress_callback("generating", "🎨 Generating knowledge diagram...")
        
        dot_code = dot_chain.invoke({"summary": summary}).content
        
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
