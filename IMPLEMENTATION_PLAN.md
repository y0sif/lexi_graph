# LexiGraph Streamlit Implementation Plan

## 🎯 Project Overview
Transform the existing CLI-based LexiGraph into a user-friendly web application using Streamlit, focusing on a clean, progress-driven user experience that shows only the final knowledge graph.

## 📋 Implementation Phases

### **Phase 1: Setup & Dependencies** ⏱️ 5 minutes
#### Tasks:
- [ ] Add Streamlit to project using `uv add streamlit`
- [ ] Create core directory structure
- [ ] Set up basic file organization

#### Commands:
```bash
uv add streamlit
mkdir core
touch core/__init__.py
touch core/pipeline.py
touch core/utils.py
touch app.py
```

---

### **Phase 2: Code Refactoring** ⏱️ 15 minutes
#### Tasks:
- [ ] Extract core logic from `main.py` into modular components
- [ ] Create reusable pipeline functions
- [ ] Maintain backward compatibility with CLI version

#### Files to Create/Modify:

##### **core/pipeline.py**
```python
# Contents:
- LLM setup (ChatOllama configuration)
- Prompt templates (summarizer_prompt, dot_prompt)  
- pipeline() function with progress callbacks
- Error handling with user-friendly messages
```

##### **core/utils.py**
```python
# Contents:
- compile_dot_to_png() function
- File management utilities (unique filenames, cleanup)
- Directory creation helpers
- Graph rendering utilities
```

##### **Updated main.py**
```python
# Contents:
- Import from core modules
- Keep existing CLI functionality
- Maintain example lecture content
```

---

### **Phase 3: Streamlit App Development** ⏱️ 25 minutes
#### Tasks:
- [ ] Create main Streamlit application
- [ ] Implement progress-driven user experience
- [ ] Add input validation and error handling

#### **app.py Structure:**

##### **Page Configuration**
```python
st.set_page_config(
    page_title="LexiGraph - Lecture to Knowledge Graph",
    page_icon="🔗",
    layout="wide"
)
```

##### **Main UI Components**
1. **Header Section**
   - Title: "🔗 LexiGraph"
   - Subtitle: "Transform lectures into visual knowledge graphs"
   - Brief description

2. **Input Section**
   - Large text area for lecture content
   - "📚 Try Example Lecture" button
   - Input validation (minimum length)

3. **Action Section**
   - "Generate Knowledge Graph" button (primary style)
   - Clear, prominent call-to-action

4. **Progress Section**
   - Dynamic status messages with emojis
   - Progress phases:
     - "🔍 Analyzing lecture content..."
     - "🎨 Generating knowledge diagram..."
     - "🖼️ Rendering visual graph..."
     - "✅ Knowledge graph ready!"

5. **Results Section**
   - Large, centered image display
   - Download button (prominent, primary style)
   - Success message

6. **Optional Features**
   - Expandable summary view
   - Clear results button
   - Error display area

---

### **Phase 4: Progress & UX Implementation** ⏱️ 15 minutes
#### Tasks:
- [ ] Implement step-by-step progress indication
- [ ] Add smooth transitions and loading states
- [ ] Create user-friendly error messages

#### **Progress Messages:**
```python
PROGRESS_MESSAGES = {
    "analyzing": "🔍 Analyzing lecture content...",
    "summarizing": "📝 Creating structured summary...", 
    "generating": "🎨 Generating knowledge diagram...",
    "rendering": "🖼️ Rendering visual graph...",
    "complete": "✅ Knowledge graph ready!"
}
```

#### **Error Handling:**
```python
ERROR_MESSAGES = {
    "connection": "❌ Connection error - Is Ollama running?",
    "analysis": "❌ Failed to analyze content - Please check your text",
    "generation": "❌ Failed to generate diagram - Please try again",
    "rendering": "❌ Failed to render graph - Please contact support"
}
```

---

### **Phase 5: Visual Polish & Enhancement** ⏱️ 10 minutes
#### Tasks:
- [ ] Add custom CSS styling
- [ ] Improve spacing and typography
- [ ] Implement responsive design
- [ ] Add visual feedback

#### **Custom CSS:**
```css
/* Custom styling for better UX */
.main-header { font-size: 3rem; text-align: center; }
.subtitle { color: #666; text-align: center; margin-bottom: 2rem; }
.generate-button { width: 100%; padding: 1rem; }
.success-message { background: #d4edda; padding: 1rem; border-radius: 8px; }
.error-message { background: #f8d7da; padding: 1rem; border-radius: 8px; }
```

#### **Image Display:**
- Full-width image display
- Automatic sizing and centering
- Subtle border/shadow effects
- Zoom capability

---

### **Phase 6: Testing & Validation** ⏱️ 10 minutes
#### Tasks:
- [ ] Test with various lecture inputs
- [ ] Verify error scenarios
- [ ] Test download functionality
- [ ] Check responsive design

#### **Test Cases:**
1. **Valid Input**: Full lecture content → Should generate graph
2. **Short Input**: Less than 50 characters → Should show validation error
3. **Empty Input**: No content → Should show helpful message
4. **LLM Error**: Ollama not running → Should show connection error
5. **Large Input**: Very long lecture → Should handle gracefully

---

## 🎨 User Experience Flow

### **Happy Path:**
1. User visits app
2. Sees clean interface with text area
3. Pastes lecture content OR clicks "Try Example"
4. Clicks "Generate Knowledge Graph"
5. Sees progress: Analyzing → Generating → Rendering → Complete
6. Views beautiful knowledge graph
7. Downloads PNG file
8. Can clear and start fresh

### **Error Scenarios:**
- **No Ollama**: Clear message with setup instructions
- **Invalid Input**: Helpful validation messages
- **Processing Error**: Retry options with guidance

---

## 🛠️ Technical Implementation Details

### **File Structure:**
```
lexi_graph/
├── main.py                 # CLI version (existing, refactored)
├── app.py                  # Streamlit web app
├── core/
│   ├── __init__.py
│   ├── pipeline.py         # Core LLM processing
│   └── utils.py           # Graph utilities
├── output/                 # Generated graphs
├── pyproject.toml         # Dependencies
└── IMPLEMENTATION_PLAN.md # This file
```

### **Session State Management:**
```python
# Track user session data
if 'graph_generated' not in st.session_state:
    st.session_state.graph_generated = False
if 'current_summary' not in st.session_state:
    st.session_state.current_summary = ""
if 'graph_path' not in st.session_state:
    st.session_state.graph_path = ""
```

### **File Naming Strategy:**
```python
# Generate unique filenames to avoid conflicts
import time
filename = f"graph_{int(time.time())}"
output_path = f"output/{filename}.png"
```

---

## 🚀 Deployment Considerations

### **Local Development:**
```bash
# Run the app locally
streamlit run app.py
```

### **Production Deployment:**
- **Streamlit Cloud**: Easy, free deployment
- **Docker**: For containerized deployment
- **Heroku/Railway**: Alternative cloud options

### **Environment Variables:**
```python
# Handle different environments
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma3n:e2b")
```

---

## 📦 Dependencies Update

### **pyproject.toml Addition:**
```toml
dependencies = [
    "dotenv>=0.9.9",
    "graphviz>=0.21", 
    "langchain-ollama>=0.3.5",
    "streamlit>=1.28.0"  # New addition
]
```

---

## 🎯 Success Criteria

### **Functional Requirements:**
- [ ] User can input lecture text
- [ ] App generates knowledge graph
- [ ] User can download PNG file
- [ ] Clear progress indication
- [ ] Proper error handling

### **UX Requirements:**
- [ ] Intuitive, clean interface
- [ ] Fast, responsive interactions
- [ ] Clear feedback on all actions
- [ ] Mobile-friendly design
- [ ] Professional appearance

### **Technical Requirements:**
- [ ] Code is modular and maintainable
- [ ] Both CLI and web versions work
- [ ] Proper error handling
- [ ] Efficient file management
- [ ] Good performance

---

## ⏱️ Estimated Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Setup & Dependencies | 5 min | 5 min |
| Code Refactoring | 15 min | 20 min |
| Streamlit App Development | 25 min | 45 min |
| Progress & UX | 15 min | 60 min |
| Visual Polish | 10 min | 70 min |
| Testing & Validation | 10 min | 80 min |

**Total Estimated Time: ~80 minutes**

---

## 🔄 Review Checklist

Before starting implementation, confirm:
- [ ] File structure is clear and logical
- [ ] UI flow matches user needs
- [ ] Progress messages are helpful
- [ ] Error handling covers all scenarios
- [ ] Technical approach is sound
- [ ] Timeline is realistic

---

## 🎉 Next Steps

1. **Review this plan** and provide feedback
2. **Approve the approach** or suggest modifications
3. **Begin Phase 1** - Setup & Dependencies
4. **Iterate through phases** with testing at each step
5. **Deploy and celebrate!** 🚀

Ready to transform LexiGraph into an amazing web app! 🎨📊
