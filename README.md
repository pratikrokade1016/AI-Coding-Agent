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

# \## Run Locally

# 

# \### 1. Open the project

# 

# Open the `coding-agent` folder in VS Code.

# 

# Open:

# 

# \*\*Terminal → New Terminal\*\*

# 

# Make sure the terminal is in:

# 

# ```text

# coding-agent

