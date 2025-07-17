import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOllama(
    model="gemma3n:e2b",
    temperature=0.1,
    num_ctx=4096,  # Context window
    base_url="http://localhost:11434",  # Default Ollama URL
)

# take lecture input from the user
lecture_input = """
Today we're going to talk about something fundamental in physics and chemistry: The States of Matter. At its core, matter is anything that has mass and occupies space. All matter exists in different forms known as states or phases.

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

Particles lose individual identity and behave as one “super-particle.”

Shows quantum effects on a macroscopic scale.

3. Transitions Between States
Matter can change from one state to another through phase changes, depending on temperature and pressure:

Melting (solid → liquid)

Freezing (liquid → solid)

Evaporation/Boiling (liquid → gas)

Condensation (gas → liquid)

Sublimation (solid → gas)

Deposition (gas → solid).
"""

# Create a prompt template for summarizing the lecture content
summarizer_prompt = ChatPromptTemplate.from_template("""
Create a hierarchical summary of this lecture content: {lecture}

Format the summary as a tree structure using dashes (-) for each level. Maintain the original language of the content. Example format:

Main Topic:
-Subtopic 1
--Detail A
--Detail B
-Subtopic 2
--Detail C
--Detail D

Return ONLY the hierarchical summary without any explanations or additional text.
                                                     
If it is already summarized in the way shown above, return it as is.
"""
)

# Combine the prompt template with the LLM
summarizer_chain = summarizer_prompt | llm

# Create a prompt template for generating DOT code

dot_prompt = ChatPromptTemplate.from_template("""
Given the following hierarchical summary of a lecture, {summary}

Create a digraph that represents the hierarchy. Use proper graphiz DOT syntax with directed edges (->) and include 'rankdir=LR' in the graph attributes. Make sure to preserve the language of the content and add appropriate styling for better visualization.

If the input given is not a summary, do not generate a DOT code fore it.
                                              
Return ONLY the DOT code without any explanations, additional text, or any `````` used for coding.
"""
)

dot_chain = dot_prompt | llm

# === 5. Compose Agents into a Pipeline ===
def pipeline(input_text: str):
    try:
        summary = summarizer_chain.invoke({"lecture": input_text}).content
        dot = dot_chain.invoke({"summary": summary}).content
    except Exception as e:
        print(f"Error during processing: {e}")
        summary = "Error generating summary."
        dot = "Error generating DOT code."
    return summary, dot

# === 6. Run Pipeline ===
summary, dot_code = pipeline(lecture_input)

# === 7. Output ===
print("\n[Summary Output]\n")
print(summary)
print("\n[DOT Code Output]\n")
print(dot_code)


# compile the DOT code into a graph png file
import graphviz

def compile_dot_to_png(dot_code: str, output_filename: str):
    try:
        graph = graphviz.Source(dot_code, format='png')
        graph.render(filename=output_filename, cleanup=True)
        print(f"Graph saved as {output_filename}.png")
    except Exception as e:
        print(f"Error generating graph: {e}")

# Compile the generated DOT code into a PNG file
output_filename = "lecture_graph"
compile_dot_to_png(dot_code, output_filename)
print(f"Graph saved as {output_filename}.png")
# Ensure the output directory exists
if not os.path.exists("output"):
    os.makedirs("output")
# Move the generated PNG file to the output directory
import shutil
shutil.move(f"{output_filename}.png", f"output/{output_filename}.png")
print(f"Graph moved to output/{output_filename}.png")
# End of the script