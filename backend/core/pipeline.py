"""
Core pipeline functions for LexiGraph
Handles multi-agent LLM processing and knowledge graph generation via multiple providers
Supports: Anthropic, OpenAI, OpenRouter
Uses specialized agents for different tasks:
- Summarization Agent: Optimized for content analysis
- Visualization Agent: Optimized for graph generation
"""

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .utils import clean_dot_code

load_dotenv()

def get_model_max_tokens(model_name: str, agent_type: str) -> int:
    """
    Get dynamic max tokens based on model capabilities and agent type
    
    Args:
        model_name (str): The model identifier
        agent_type (str): Type of agent (validation, summarization, visualization)
    
    Returns:
        int: Optimal max_tokens for the model and agent combination
    """
    # Known model context window limits (output token limits)
    model_limits = {
        # Anthropic models
        "claude-opus-4-1-20250805": 32000,       # 32k context window
        "claude-opus-4-20250514": 32000,         # 32k context window
        "claude-sonnet-4-20250514": 64000,       # 64k context window
        "claude-3-7-sonnet-20250219": 64000,     # 64k context window
        "claude-3-5-haiku-20241022": 8000,       # 8k context window
        
        # OpenAI models
        "gpt-5": 128000,                         # 128k context window
        "gpt-4.1": 32000,                        # 32k context window
        "gpt-4o": 128000,                        # 128k context window
        "gpt-4o-mini": 16000,                    # 16k context window
        "gpt-4-turbo": 4000,                     # 4k context window
        
        # OpenRouter Anthropic models
        "anthropic/claude-opus-4-1-20250805": 32000,     # 32k context window
        "anthropic/claude-opus-4-20250514": 32000,       # 32k context window
        "anthropic/claude-sonnet-4-20250514": 64000,     # 64k context window
        "anthropic/claude-3-7-sonnet-20250219": 64000,   # 64k context window
        "anthropic/claude-3-5-haiku-20241022": 8000,     # 8k context window
        
        # OpenRouter OpenAI models
        "openai/gpt-5": 128000,                  # 128k context window
        "openai/gpt-4.1": 32000,                 # 32k context window
        "openai/gpt-4o": 128000,                 # 128k context window
        "openai/gpt-4o-mini": 16000,             # 16k context window
        "openai/gpt-4-turbo": 4000,              # 4k context window
        
        # OpenRouter free models (with real context windows)
        "deepseek/deepseek-chat-v3-0324:free": 160000,  # DeepSeek R1: 160k
        "deepseek/deepseek-r1-0528:free": 160000,       # DeepSeek R1: 160k
        "qwen/qwen3-coder:free": 40000,                 # Qwen 3 4B: 40k
        "deepseek/deepseek-r1:free": 160000,            # DeepSeek R1: 160k
        "moonshotai/kimi-k2:free": 32000,               # Kimi 2: 32k
        "qwen/qwen3-235b-a22b:free": 41000,             # Qwen3 235B A22B: 41k
        "meta-llama/llama-3.3-70b-instruct:free": 130000, # Llama 3.3: 130k (using 3.2 data)
        "google/gemma-3n-e4b-it:free": 2000,            # Gemma 3N4B: 2k
        "mistralai/mistral-small-3.1-24b-instruct:free": 95000, # Mistral Small 3.1: 95k
        "openai/gpt-oss-20b:free": 130000,              # GPT-OSS-20B: 130k
        "google/gemma-3n-e2b-it:free": 2000,            # Gemma 3N2B: 2k
        "meta-llama/llama-3.2-3b-instruct:free": 130000, # Llama 3.2 3B: 130k
        "qwen/qwen3-4b:free": 40000,                    # Qwen 3 4B: 40k
        "mistralai/mistral-7b-instruct:free": 95000,    # Using Mistral Small data: 95k
        "google/gemma-2-9b-it:free": 8000,              # Gemma 2 9B: 8k
        "google/gemma-3-27b-it:free": 8000,             # Using Gemma 2 data: 8k
    }
    
    # Agent type scaling factors (percentage of max tokens to use)
    scaling_factors = {
        "validation": 0.15,      # 15% - short responses for classification
        "summarization": 0.75,   # 75% - detailed hierarchical summaries
        "visualization": 0.70    # 70% - complex DOT code structures
    }
    
    # Get base limit for the model
    if model_name in model_limits:
        base_limit = model_limits[model_name]
    else:
        # Smart fallbacks based on model name patterns
        model_lower = model_name.lower()
        if "haiku" in model_lower:
            base_limit = 8192
        elif "sonnet" in model_lower:
            base_limit = 8000
        elif "opus" in model_lower:
            base_limit = 8000
        elif "gpt-4o-mini" in model_lower:
            base_limit = 16384
        elif "gpt" in model_lower:
            base_limit = 4096
        elif "deepseek" in model_lower or "qwen" in model_lower:
            base_limit = 8000
        elif "llama" in model_lower or "gemma" in model_lower:
            base_limit = 8000
        elif "mistral" in model_lower:
            base_limit = 8000
        else:
            base_limit = 4000  # Conservative fallback for unknown models
    
    # Apply scaling factor for agent type
    scaled_limit = int(base_limit * scaling_factors.get(agent_type, 0.5))
    
    # Ensure minimum viable limits
    min_limits = {
        "validation": 500,
        "summarization": 2000,
        "visualization": 2000
    }
    
    final_limit = max(scaled_limit, min_limits.get(agent_type, 1000))
    
    print(f"🎯 Model: {model_name}, Agent: {agent_type}, Base: {base_limit}, Scaled: {final_limit}")
    
    return final_limit

def get_llm_instance(model_name=None, temperature=0.1, max_tokens=4000, agent_type="general"):
    """
    Create LLM instance based on environment configuration with dynamic token limits
    Supports multiple providers: Anthropic, OpenAI, OpenRouter
    """
    provider = os.getenv("PROVIDER", "anthropic").lower()
    model = model_name or os.getenv("MODEL_NAME", "claude-3-5-haiku-20241022")
    
    # Use dynamic max_tokens based on model capabilities and agent type
    if agent_type != "general":
        max_tokens = get_model_max_tokens(model, agent_type)
    
    print(f"🤖 Creating LLM instance: provider={provider}, model={model}, max_tokens={max_tokens}, agent={agent_type}")
    
    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
        )
    elif provider == "openai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=max_tokens,
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            max_tokens=max_tokens,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def create_summarization_agent():
    """Create and configure the LLM instance specialized for summarization"""
    return get_llm_instance(agent_type="summarization")

def create_visualization_agent():
    """Create and configure the LLM instance specialized for DOT code generation"""
    return get_llm_instance(agent_type="visualization")

def create_validation_agent():
    """Create and configure the LLM instance specialized for content validation"""
    return get_llm_instance(agent_type="validation")

def get_agent_info():
    """
    Returns information about the specialized agents
    
    Returns:
        dict: Information about each agent's configuration and purpose
    """
    return {
        "validation_agent": {
            "purpose": "Content type classification and input filtering",
            "temperature": 0.1,
            "max_tokens": 1000,
            "optimization": "Fast and reliable content validation",
            "provider": "Anthropic",
            "model": "claude-3-5-haiku-20241022"
        },
        "summarization_agent": {
            "purpose": "Content analysis and structured summarization",
            "temperature": 0.1,
            "max_tokens": 8000,
            "optimization": "Consistent, hierarchical output",
            "provider": "Anthropic",
            "model": "claude-3-5-haiku-20241022"
        },
        "visualization_agent": {
            "purpose": "DOT code generation and graph syntax",
            "temperature": 0.1,
            "max_tokens": 8000,
            "optimization": "Precise syntax, complex structures",
            "provider": "Anthropic", 
            "model": "claude-3-5-haiku-20241022"
        }
    }

def create_prompts():
    """Create prompt templates for validation, summarization and DOT generation"""
    
    validation_prompt = ChatPromptTemplate.from_template("""You are a content validation specialist. Your job is to determine if the provided text contains educational or lecture-style content suitable for knowledge graph creation.

VALID CONTENT TYPES:
- Academic lectures or presentations
- Educational materials and explanations
- Technical documentation and tutorials
- Course content or training materials
- Informational articles with learning value
- Scientific or research explanations
- How-to guides with educational content

INVALID CONTENT TYPES:
- Personal stories, narratives, or diary entries
- Chat conversations or casual dialogue
- News articles without educational value
- Poetry, creative writing, or fiction
- Simple lists without explanatory content
- Random text or gibberish
- Very short text (less than 100 words)
- Marketing or promotional content

Your job is to classify the content type, NOT evaluate its structure or organization.

Respond with EXACTLY one word: either "VALID" or "INVALID"

Content to validate: {input_text}""")
    
    summarizer_prompt = ChatPromptTemplate.from_template("""CRITICAL LANGUAGE REQUIREMENT: You MUST write your entire summary in the EXACT SAME LANGUAGE as the input lecture content. If the lecture is in Arabic, write EVERYTHING in Arabic. If in English, write EVERYTHING in English. Do NOT mix languages or translate anything.

I want you to generate a detailed, hierarchical summary of a topic I provide, using the exact format described below. Your output should follow these formatting and content guidelines:

LANGUAGE RULE: Match the input language exactly - Arabic content gets Arabic summary, English content gets English summary, etc.

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
- What it does
- Where or when it is used
- A simple real-world example
- Important strengths, weaknesses, or notes

Cover both broad and detailed information
For example, if the topic includes "Supervised Learning," list common algorithms under it, and for each algorithm, include further sub-points explaining its function and use cases.

Avoid unnecessary repetition or filler
Keep the summary concise but complete. Focus on clarity, logical organization, and informativeness.

Use this format as a style guide (NOTE: This example is in English, but adapt the structure to match your input language):

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

REMEMBER: Write your summary in the SAME LANGUAGE as the lecture content below.

Lecture content: {lecture}

Return ONLY the hierarchical summary in the same language as the input, without any explanations or additional text.""")

    dot_prompt = ChatPromptTemplate.from_template("""CRITICAL LANGUAGE REQUIREMENT: You MUST write ALL node labels in the EXACT SAME LANGUAGE as the input summary. If the summary is in Arabic, ALL labels must be in Arabic. If in English, ALL labels must be in English. Do NOT translate or mix languages.

I want you to generate a Graphviz DOT file that visually represents a hierarchical summary of a topic. The input is a structured summary written in the following indentation style:

Main Topic:
- Subtopic
-- Sub-subtopic
--- Detail

Your output should follow these formatting and structural guidelines:

LANGUAGE RULE: All node labels must match the language of the input summary exactly.

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
CRITICAL COLOR GUIDELINES:
- Use fillcolor (NEVER color) for background colors when style=filled is used
- Always specify explicit fontcolor for text visibility
- ONLY use light colors for good text readability: white, yellow, cyan, pink, orange
- AVOID dark colors like blue, green, red, purple as they make text hard to read
- For text color: use fontcolor=black for light backgrounds, fontcolor=white for dark backgrounds
- Never use black for the background of a node


Node naming convention:
- Use simple identifiers like: AI, ML, SupervisedLearning, etc.
- Put the actual text in the label attribute (in the same language as the summary)
- Example: SupervisedLearning [label="Supervised Learning\\nTrains on labeled data", fillcolor=yellow, fontcolor=black];

Edges
Connect nodes based on their parent-child relationships using simple node identifiers.

Example of correct syntax with color grouping (NOTE: This example uses English labels, but you must use the language of your input):
digraph TopicSummary {{
    rankdir=LR;
    node [shape=box, style=filled];

    // Root node - use light colors for good text contrast
    AI [label="Artificial Intelligence", fillcolor=white, fontcolor=black];
    
    // Children of AI (same color group) - use light colors
    ML [label="Machine Learning", fillcolor=yellow, fontcolor=black];
    NLP [label="Natural Language Processing", fillcolor=yellow, fontcolor=black];
    
    // Children of ML (same color group) - use different light colors for grouping
    SupervisedLearning [label="Supervised Learning\\nTrains on labeled data", fillcolor=cyan, fontcolor=black];
    UnsupervisedLearning [label="Unsupervised Learning\\nFinds patterns in data", fillcolor=cyan, fontcolor=black];
    
    // Edges
    AI -> ML;
    AI -> NLP;
    ML -> SupervisedLearning;
    ML -> UnsupervisedLearning;
}} 

Goal:
Produce a clean, valid DOT file with proper syntax that accurately reflects the logical structure of the input summary, with nodes visually grouped by color based on their parent relationships.
REMEMBER: Write ALL node labels in the SAME LANGUAGE as the input summary.

Hierarchical summary: {summary}

Return ONLY the DOT code without any explanations, additional text, or any ` used for annotating code, so don't put the code inside markdown syntax.""")
    
    return validation_prompt, summarizer_prompt, dot_prompt

def pipeline(input_text: str, progress_callback=None):
    """
    Multi-agent pipeline function that processes lecture text into knowledge graph
    Uses specialized agents for different tasks:
    - Validation Agent: Content type classification and input filtering
    - Summarization Agent: Optimized for content analysis and structured summarization
    - Visualization Agent: Optimized for DOT code generation and graph syntax
    
    Args:
        input_text (str): The content to process
        progress_callback (callable): Optional callback function for progress updates
    
    Returns:
        tuple: (summary, dot_code) or (error_message, None) on failure
    """
    try:
        # Create specialized agents using environment variable
        validation_agent = create_validation_agent()
        summarization_agent = create_summarization_agent()
        visualization_agent = create_visualization_agent()
        
        # Get prompts
        validation_prompt, summarizer_prompt, dot_prompt = create_prompts()
        
        # Create specialized chains
        validation_chain = validation_prompt | validation_agent
        summarizer_chain = summarizer_prompt | summarization_agent
        dot_chain = dot_prompt | visualization_agent
        
        # Step 1: Validation Agent checks content type
        if progress_callback:
            progress_callback("validating", "🔍 Validation agent checking content type...")
        
        validation_result = validation_chain.invoke({"input_text": input_text}).content.strip().upper()
        
        # Check if content is valid for processing
        if "INVALID" in validation_result:
            error_msg = "The provided content doesn't appear to be educational material suitable for creating knowledge graphs. Please provide lecture notes, tutorials, or informational content with learning concepts."
            print(f"❌ Content validation failed: {validation_result}")
            return error_msg, None
        
        # Step 2: Summarization Agent processes the lecture
        if progress_callback:
            progress_callback("analyzing", "� Summarization agent analyzing content...")
        
        summary = summarizer_chain.invoke({"lecture": input_text}).content
        
        # Step 3: Visualization Agent generates DOT code
        if progress_callback:
            progress_callback("generating", "🎨 Visualization agent creating graph...")
        
        print("🤖 Requesting DOT code from visualization agent...")
        dot_code_raw = dot_chain.invoke({"summary": summary}).content
        print(f"📝 Raw DOT code received (length: {len(dot_code_raw)} chars)")
        
        print("🧹 Cleaning DOT code...")
        dot_code = clean_dot_code(dot_code_raw)
        print(f"📝 Cleaned DOT code (length: {len(dot_code)} chars)")
        
        if not dot_code.strip():
            error_msg = "Unable to generate graph code from the content. Please try with different text or a different AI model."
            print(f"❌ No valid DOT code generated by visualization agent")
            print(f"📝 Raw output from agent:\n{'-'*50}")
            print(dot_code_raw)
            print(f"{'-'*50}")
            return error_msg, None
        
        # Basic DOT structure validation
        if not any(keyword in dot_code.lower() for keyword in ['digraph', 'graph']):
            error_msg = "Generated graph code is malformed. Please try again with different content or model."
            print(f"❌ Generated code does not contain 'digraph' or 'graph' keyword")
            print(f"📝 Generated code:\n{'-'*50}")
            print(dot_code)
            print(f"{'-'*50}")
            return error_msg, None
        
        print("✅ DOT code generation completed successfully")
        return summary, dot_code
        
    except Exception as e:
        # Log detailed error for debugging
        detailed_error = f"Pipeline error: {e}"
        print(detailed_error)
        
        # Provide user-friendly error message
        user_friendly_error = "An error occurred while processing your content. Please try again."
        
        # Handle specific common errors
        error_str = str(e).lower()
        if "rate limit" in error_str or "quota" in error_str:
            user_friendly_error = "API rate limit reached. Please wait a moment and try again."
        elif "api key" in error_str or "authentication" in error_str:
            user_friendly_error = "Authentication failed. Please check your API key."
        elif "timeout" in error_str:
            user_friendly_error = "Request timed out. Please try with shorter content."
        elif "max_tokens" in error_str:
            user_friendly_error = "Content is too long for the selected model. Please try shorter text."
        
        return user_friendly_error, None

# Example lecture content for the web app
EXAMPLE_LECTURE = """Welcome to this short lecture on Artificial Intelligence. Let’s start with the basics. Artificial Intelligence, or AI, refers to the capability of machines to perform tasks that typically require human intelligence—things like understanding language, recognizing images, or making decisions. Within AI, one of the most important and widely used branches is Machine Learning, or ML. Machine Learning is all about teaching computers to learn from data. Instead of programming every rule manually, we feed the machine examples, and it learns patterns or rules from that data on its own.

Machine learning comes in several types. The first is supervised learning, where we train the model using labeled data—that means we give it both the input and the correct output. For example, if we want to train a model to detect spam emails, we show it lots of examples of emails labeled as “spam” or “not spam,” and the model learns to predict that label. The second type is unsupervised learning, where the data has no labels at all. The algorithm’s job is to find hidden patterns or groupings. A good example here would be clustering customers based on their shopping behavior—without knowing their categories beforehand. Then we have semi-supervised learning, which is a mix of both: it uses a small amount of labeled data and a larger amount of unlabeled data to improve learning accuracy.

Another major category is reinforcement learning. Here, the model—or we call it an agent—learns by interacting with an environment and receiving feedback in the form of rewards or penalties. A classic example is training a robot to walk or teaching an AI to play games like chess or Go. It tries actions, sees the result, and adjusts its behavior over time to maximize rewards.

Now, within machine learning, there's a very powerful subfield called deep learning. Deep learning uses neural networks with many layers, and it has completely transformed what we can do with AI. These deep neural networks are excellent at automatically learning complex features from data, especially in areas like image recognition, speech processing, and natural language understanding. Deep learning is what powers technologies like self-driving cars, facial recognition, and even language models like ChatGPT.

To summarize: AI is the broad field. Machine learning is a subset that lets computers learn from data. And deep learning is a further subset that uses multi-layered neural networks to learn high-level patterns. Each type of learning—supervised, unsupervised, semi-supervised, and reinforcement—has its strengths depending on the problem you’re trying to solve. And understanding which one to use is a big part of becoming proficient in AI."""
