# 📚 Public Library Information Assistant

A smart chatbot application that provides information about library services using Google's Generative AI API. The assistant can answer questions about membership rules, borrowing procedures, overdue policies, and digital resources.

## 🎯 Features

- **Library Services Explainer**: Get clear explanations about library rules and procedures
- **Secure API Key Management**: API keys are stored in environment variables, not hardcoded
- **Multiple Interfaces**: Use via terminal CLI or web-based Streamlit UI
- **Professional Python Module**: Reusable `LibraryAssistant` class for integration

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Google Generative AI API key (get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Syed8855/v-cube-hackthon.git
   cd v-cube-hackthon
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

## 📖 Usage

### Option 1: CLI (Terminal)

Run the assistant in interactive terminal mode:

```bash
python library_assistant.py
```

This starts an interactive chat session where you can ask questions about library services.

**Example:**
```
You: How many books can I borrow at once?
🤔 Thinking...
Assistant: [Response about borrowing limits]
```

### Option 2: Web UI (Streamlit)

Launch the web interface:

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

## 🏗️ Project Structure

```
v-cube-hackthon/
├── app.py                   # Streamlit web interface
├── library_assistant.py     # Main Python module with LibraryAssistant class
├── V_cube_Hackthon.ipynb   # Original Jupyter notebook
├── requirements.txt         # Python dependencies
├── .env.example            # Template for environment variables
├── .gitignore              # Git ignore rules (includes .env for security)
└── README.md               # This file
```

## 📝 Code Structure

### `LibraryAssistant` Class

The core interface is the `LibraryAssistant` class in `library_assistant.py`:

```python
from library_assistant import LibraryAssistant

# Initialize with automatic .env loading
assistant = LibraryAssistant()

# Get a response
response = assistant.get_response("What is the borrowing limit?")
print(response)

# Start interactive chat
assistant.chat_session()
```

#### Constructor Parameters:
- `api_key` (str, optional): Google API key. If None, loads from `.env`
- `model_name` (str): Model to use (default: "gemini-2.5-flash")

#### Methods:
- `get_response(user_input: str) -> str`: Get a response to a library question
- `chat_session()`: Start an interactive terminal chat session

## 🔒 Security

- **No hardcoded secrets**: API keys are never committed to the repository
- **Environment variables**: All sensitive data is stored in `.env` file
- **.gitignore protection**: `.env` file is in `.gitignore` to prevent accidental commits
- **Template file**: `.env.example` shows the required variables

## ⚠️ Limitations

The assistant is designed specifically to explain library services and has built-in restrictions:

- ❌ **Cannot** issue books
- ❌ **Cannot** manage user accounts
- ❌ **Cannot** perform transactions
- ❌ **Cannot** answer non-library-related questions

When asked to perform restricted actions, the assistant politely refuses.

## 🛠️ Customization

### Modify System Prompt

Edit the `SYSTEM_PROMPT` in `library_assistant.py` to change the assistant's behavior.

### Change Model

Initialize with a different model:
```python
assistant = LibraryAssistant(model_name="gemini-1.5-pro")
```

## 📚 Technology Stack

- **Framework**: Streamlit (web UI)
- **AI**: Google Generative AI (Gemini API)
- **Language**: Python 3.7+
- **Configuration**: python-dotenv (environment management)

## 📋 Requirements

See `requirements.txt` for all dependencies:
- `google-generativeai`: Google's Generative AI library
- `streamlit`: Web application framework
- `python-dotenv`: Environment variable management

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is part of the V-Cube Hackathon.

## 🙋 Support

For issues or questions:
1. Check the `.env.example` file to ensure your setup is correct
2. Verify your Google API key is valid
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

## 📌 Notes

- The original notebook (`V_cube_Hackthon.ipynb`) contains the initial implementation
- The refactored code follows Python best practices with proper modularization
- API key security has been improved by moving to environment variables