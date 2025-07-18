"""
Core pipeline functions for LexiGraph
Handles multi-agent LLM processing and knowledge graph generation
Uses specialized agents for different tasks:
- Summarization Agent: Optimized for content analysis
- Visualization Agent: Optimized for graph generation
"""

import os
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from .utils import clean_dot_code

load_dotenv()

def create_summarization_agent():
    """Create and configure the LLM instance specialized for summarization"""
    return ChatCohere(
        model=os.getenv("COHERE_MODEL", "command-r-plus"),
        temperature=0.1,  
        cohere_api_key=os.getenv("COHERE_API_KEY"),
        max_tokens=4000,  
    )

def create_visualization_agent():
    """Create and configure the LLM instance specialized for DOT code generation"""
    return ChatCohere(
        model=os.getenv("COHERE_MODEL", "command-r-plus"),
        temperature=0.1,  
        cohere_api_key=os.getenv("COHERE_API_KEY"),
        max_tokens=6000,  
    )

def get_agent_info():
    """
    Returns information about the specialized agents
    
    Returns:
        dict: Information about each agent's configuration and purpose
    """
    return {
        "summarization_agent": {
            "purpose": "Content analysis and structured summarization",
            "temperature": 0.1,
            "max_tokens": 4000,
            "optimization": "Consistent, hierarchical output"
        },
        "visualization_agent": {
            "purpose": "DOT code generation and graph syntax",
            "temperature": 0.1,
            "max_tokens": 6000,
            "optimization": "Precise syntax, complex structures"
        }
    }

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

IMPORTANT SYNTAX RULES:
- Node names must be valid identifiers (letters, numbers, underscores only) or quoted strings
- Use quoted strings for node names with spaces or special characters
- All text content should go in the label attribute, not the node name
- Edges connect node identifiers, not labels or descriptions

Graph orientation
Set the graph direction to left-to-right using rankdir=LR.

Nodes and Color Grouping
Each item from the hierarchy should be represented as a separate node. Use shape=box and style=filled for clarity.

Node naming convention:
- Use simple identifiers like: AI, ML, SupervisedLearning, etc.
- Put the actual text in the label attribute
- Example: SupervisedLearning [label="Supervised Learning\\nTrains on labeled data", color=lightblue];

Edges
Connect nodes based on their parent-child relationships using simple node identifiers.

Example of correct syntax with color grouping:
digraph TopicSummary {{
    rankdir=LR;
    node [shape=box, style=filled];

    // Root node
    AI [label="Artificial Intelligence", color=lightgray];
    
    // Children of AI (same color group)
    ML [label="Machine Learning", color=lightblue];
    NLP [label="Natural Language Processing", color=lightblue];
    
    // Children of ML (same color group)
    SupervisedLearning [label="Supervised Learning\\nTrains on labeled data", color=lightgreen];
    UnsupervisedLearning [label="Unsupervised Learning\\nFinds patterns in data", color=lightgreen];
    
    // Edges
    AI -> ML;
    AI -> NLP;
    ML -> SupervisedLearning;
    ML -> UnsupervisedLearning;
}} 

Goal:
Produce a clean, valid DOT file with proper syntax that accurately reflects the logical structure of the input summary, with nodes visually grouped by color based on their parent relationships.

Hierarchical summary: {summary}

Return ONLY the DOT code without any explanations, additional text, or any ` used for annotating code, so don't put the code inside markdown syntax.""")
    
    return summarizer_prompt, dot_prompt

def pipeline(input_text: str, progress_callback=None):
    """
    Multi-agent pipeline function that processes lecture text into knowledge graph
    Uses specialized agents for different tasks:
    - Summarization Agent: Optimized for content analysis and structured summarization
    - Visualization Agent: Optimized for DOT code generation and graph syntax
    
    Args:
        input_text (str): The lecture content to process
        progress_callback (callable): Optional callback function for progress updates
    
    Returns:
        tuple: (summary, dot_code) or (error_message, None) on failure
    """
    try:
        # Create specialized agents
        summarization_agent = create_summarization_agent()
        visualization_agent = create_visualization_agent()
        
        # Get prompts
        summarizer_prompt, dot_prompt = create_prompts()
        
        # Create specialized chains
        summarizer_chain = summarizer_prompt | summarization_agent
        dot_chain = dot_prompt | visualization_agent
        
        # Step 1: Summarization Agent processes the lecture
        if progress_callback:
            progress_callback("analyzing", "🔍 Summarization agent analyzing content...")
        
        summary = summarizer_chain.invoke({"lecture": input_text}).content
        
        # Step 2: Visualization Agent generates DOT code
        if progress_callback:
            progress_callback("generating", "🎨 Visualization agent creating graph...")
        
        dot_code_raw = dot_chain.invoke({"summary": summary}).content
        dot_code = clean_dot_code(dot_code_raw)
        
        return summary, dot_code
        
    except Exception as e:
        error_msg = f"Error during processing: {e}"
        print(error_msg)
        return error_msg, None

# Example lecture content for the web app
EXAMPLE_LECTURE = """Welcome to this short lecture on Artificial Intelligence. Let’s start with the basics. Artificial Intelligence, or AI, refers to the capability of machines to perform tasks that typically require human intelligence—things like understanding language, recognizing images, or making decisions. Within AI, one of the most important and widely used branches is Machine Learning, or ML. Machine Learning is all about teaching computers to learn from data. Instead of programming every rule manually, we feed the machine examples, and it learns patterns or rules from that data on its own.

Machine learning comes in several types. The first is supervised learning, where we train the model using labeled data—that means we give it both the input and the correct output. For example, if we want to train a model to detect spam emails, we show it lots of examples of emails labeled as “spam” or “not spam,” and the model learns to predict that label. The second type is unsupervised learning, where the data has no labels at all. The algorithm’s job is to find hidden patterns or groupings. A good example here would be clustering customers based on their shopping behavior—without knowing their categories beforehand. Then we have semi-supervised learning, which is a mix of both: it uses a small amount of labeled data and a larger amount of unlabeled data to improve learning accuracy.

Another major category is reinforcement learning. Here, the model—or we call it an agent—learns by interacting with an environment and receiving feedback in the form of rewards or penalties. A classic example is training a robot to walk or teaching an AI to play games like chess or Go. It tries actions, sees the result, and adjusts its behavior over time to maximize rewards.

Now, within machine learning, there's a very powerful subfield called deep learning. Deep learning uses neural networks with many layers, and it has completely transformed what we can do with AI. These deep neural networks are excellent at automatically learning complex features from data, especially in areas like image recognition, speech processing, and natural language understanding. Deep learning is what powers technologies like self-driving cars, facial recognition, and even language models like ChatGPT.

To summarize: AI is the broad field. Machine learning is a subset that lets computers learn from data. And deep learning is a further subset that uses multi-layered neural networks to learn high-level patterns. Each type of learning—supervised, unsupervised, semi-supervised, and reinforcement—has its strengths depending on the problem you’re trying to solve. And understanding which one to use is a big part of becoming proficient in AI."""
