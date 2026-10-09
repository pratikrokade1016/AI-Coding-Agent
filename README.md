# \# AI Coding Agent

# 

# A small AI-powered coding agent that takes a developer task in natural language, understands the project structure, identifies the relevant files, proposes code changes, applies them, and validates the result with tests.

# 

# \## What it does

# 

# The agent follows a simple workflow:

# 

# 1\. Understands the developer's request

# 2\. Inspects the available codebase

# 3\. Identifies relevant files

# 4\. Creates an implementation plan

# 5\. Generates the required code changes

# 6\. Shows the proposed changes as a diff

# 7\. Applies the changes to the project

# 8\. Runs tests and displays the result

# 

# The goal is to provide a practical coding-assistant workflow rather than a large autonomous system.

# 

# \## Approach

# 

# The application uses Streamlit for the interface and an LLM through OpenRouter for task understanding, planning, and code generation.

# 

# The coding agent uses filesystem tools to discover and read project files. The LLM returns the required file changes, while Python handles file operations, diff generation, workspace safety, and test execution.

# 

# This keeps the LLM responsible for understanding and generating code while deterministic Python components handle the actual project changes and validation.

# 

# \## Tech Stack

# 

# \- Python

# \- Streamlit

# \- OpenRouter LLM

# \- OpenAI Python SDK

# \- Pydantic

# \- Pytest

# \- FastAPI (sample project)

# 

## Running the Project Locally:-

Follow these steps to run the AI Coding Agent on your local machine.

### 1. Prerequisites

Make sure you have the following installed:

- Python 3.10 or later
- Git
- Visual Studio Code

### 2. Open the Project

Clone the repository and open the project folder in VS Code.

```powershell
git clone https://github.com/pratikrokade1016/AI-Coding-Agent.git
cd AI-Coding-Agent
```

If you have already downloaded or cloned the project, open the existing `coding-agent` folder in VS Code instead.

### 3. Open the Terminal

In VS Code, select **Terminal → New Terminal**.

Make sure the terminal is running from the project root directory, where `requirements.txt` is located.

### 4. Create and Activate a Virtual Environment

Create a Python virtual environment:

```powershell
python -m venv venv
```

Activate it in Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If activation is successful, your terminal will display `(venv)`.

### 5. Install Dependencies

Install the required Python packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Configure the OpenRouter API Key

Create a `.env` file in the project root by copying `.env.example`.

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your OpenRouter API key and model configuration using the variable names provided in `.env.example`.

Keep your actual API key private. Do not commit `.env` to GitHub.

### 7. Run the Application

From the project root, execute:

```powershell
python -m streamlit run app/streamlit_app.py
```

Streamlit will provide a local URL, usually:

`http://localhost:8501`

Open the URL in your browser to access the AI Coding Agent.

### 8. Test the Application

1. Enter a coding task in natural language.
2. Review the generated implementation plan.
3. Inspect the relevant source files.
4. Generate and review the proposed code diff.
5. Apply the changes when ready.
6. Run the validation step and review the test results.

### Troubleshooting

- **Python is not recognized:** Try using `py` instead of `python` in the commands.
- **Activation is blocked:** Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in PowerShell, then activate the environment again.
- **Missing dependencies:** Confirm the virtual environment is active and reinstall the packages.
- **API errors:** Verify that your OpenRouter API key and model configuration are correct.
- **Port already in use:** Run Streamlit with another port, for example `python -m streamlit run app/streamlit_app.py --server.port 8502`.

