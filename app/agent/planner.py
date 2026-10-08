import json
import os
import re
from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

load_dotenv()


def get_config(name: str, default: str | None = None) -> str | None:
    """Read configuration from environment variables or Streamlit secrets."""
    value = os.getenv(name)

    if value:
        return value

    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


class RelevantFile(BaseModel):
    path: str
    reason: str


class AgentPlan(BaseModel):
    task_summary: str
    relevant_files: List[RelevantFile]
    plan: List[str]
    assumptions: List[str]


def _extract_json(text: str) -> dict:
    """
    Extract a JSON object from the LLM response.

    Handles:
    - plain JSON
    - ```json ... ```
    - extra text surrounding JSON
    """

    if not text:
        raise ValueError("LLM returned an empty response.")

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    text = text.strip()

    # Try direct JSON first
    try:
        result = json.loads(text)

        if not isinstance(result, dict):
            raise ValueError("LLM response JSON is not an object.")

        return result

    except json.JSONDecodeError:
        pass

    # Try extracting the first JSON object
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)

    if not match:
        raise ValueError(
            "Could not find a valid JSON object in the LLM response.\n\n"
            f"Raw response:\n{text}"
        )

    try:
        result = json.loads(match.group(0))

        if not isinstance(result, dict):
            raise ValueError("Extracted JSON is not an object.")

        return result

    except json.JSONDecodeError as exc:
        raise ValueError(
            "The LLM returned malformed JSON.\n\n"
            f"Raw response:\n{text}"
        ) from exc


def create_plan(task: str, files: list[dict]) -> AgentPlan:
    """
    Ask Nemotron to understand the coding task and identify
    relevant files.
    """

    api_key = get_config("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing. "
            "Configure it in .env for local use or Streamlit Secrets for deployment."
        )

    model = get_config(
        "OPENROUTER_MODEL",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
    )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    file_listing = "\n".join(
        f"- {item}" for item in files
    )

    system_prompt = """
You are a software engineering coding agent.

Analyze the developer task and the provided project file list.

Identify:
1. What the developer wants
2. Which files are relevant
3. A concise implementation plan
4. Any important assumptions

Return ONLY valid JSON.

Required JSON structure:

{
  "task_summary": "string",
  "relevant_files": [
    {
      "path": "relative/file/path",
      "reason": "why this file is relevant"
    }
  ],
  "plan": [
    "step 1",
    "step 2"
  ],
  "assumptions": [
    "assumption 1"
  ]
}

Rules:
- Only select files from the provided file list.
- Do not invent files.
- Keep the plan concise.
- Do not use markdown.
- Do not wrap the JSON in code fences.
"""

    user_prompt = f"""
Developer task:

{task}

Project files:

{file_listing}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=3000,
        )

        if not response.choices:
            raise RuntimeError(
                "OpenRouter returned no choices."
            )

    except Exception as first_error:

        # Free model providers can occasionally return an empty
        # completion. Retry once before failing the agent.
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_tokens=3000,
            )

        except Exception as second_error:

            raise RuntimeError(
                "OpenRouter planner request failed after retry.\n\n"
                f"First attempt: {first_error}\n"
                f"Second attempt: {second_error}"
            ) from second_error

    if not response.choices:
        raise RuntimeError(
            "OpenRouter returned no choices after retry.\n"
            f"Model: {getattr(response, 'model', None)}\n"
            f"Response ID: {getattr(response, 'id', None)}\n"
            f"Provider: {getattr(response, 'provider', None)}"
        )

    message = response.choices[0].message

    if not message:
        raise RuntimeError(
            "Nemotron returned an empty message."
        )

    content = message.content

    if not content:
        raise RuntimeError(
            "Nemotron returned no text content.\n\n"
            f"Finish reason: "
            f"{response.choices[0].finish_reason}\n"
            f"Tool calls: {message.tool_calls}"
        )

    try:
        data = _extract_json(content)

    except ValueError as exc:
        raise RuntimeError(
            f"Could not parse Nemotron's response.\n\n{exc}"
        ) from exc

    try:
        return AgentPlan.model_validate(data)

    except ValidationError as exc:
        raise RuntimeError(
            "Nemotron returned JSON, but it does not match "
            "the expected agent-plan structure.\n\n"
            f"Validation error:\n{exc}\n\n"
            f"Returned JSON:\n{json.dumps(data, indent=2)}"
        ) from exc