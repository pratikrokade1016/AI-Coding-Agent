import os
import json
import difflib
import time
from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()


class FileChange(BaseModel):
    operation: str
    path: str
    explanation: str
    patch: str
    content: str | None = None


class PatchResult(BaseModel):
    summary: str
    changes: List[FileChange]


def generate_patch(
    task: str,
    plan: str,
    file_contents: dict[str, str],
) -> PatchResult:

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing. Check your .env file."
        )

    model = os.getenv(
        "OPENROUTER_MODEL",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
    )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    source_context = "\n".join(
        f"""
===== FILE: {path} =====

{content}

===== END FILE =====
"""
        for path, content in file_contents.items()
    )

    system_prompt = """
You are an expert software engineer acting as a coding agent.

You receive:
1. A developer task
2. An implementation plan
3. The actual source files inspected from a project

Determine the smallest correct set of code changes.

IMPORTANT:
- Base decisions on the supplied source code.
- Do not invent existing files, APIs, frameworks, databases, or functionality.
- Preserve existing behavior unless the task requires changing it.
- Preserve the project's existing coding style.
- Keep changes minimal.
- Add or modify tests when appropriate.
- You may CREATE a new file when the task requires it.
- You may MODIFY existing files.
- You may DELETE a file only when explicitly required.
- Never access paths outside the project.
- Do not generate unified diff syntax.
- Return complete file contents for CREATE and MODIFY operations.
- For DELETE operations, content must be null.

Return ONLY valid JSON.

Required structure:

{
  "summary": "Short explanation",
  "changes": [
    {
      "operation": "modify",
      "path": "relative/path.py",
      "explanation": "Why this changes",
      "content": "Complete updated file content"
    }
  ]
}

Allowed operations:
- modify
- create
- delete

For MODIFY:
The path must already exist in the supplied source files.

For CREATE:
The path must be a new project-relative path.

For DELETE:
Only use it when clearly required by the task.
"""

    user_prompt = f"""
Developer task:

{task}

Implementation plan:

{plan}

Actual inspected source files:

{source_context}
"""

    last_error = None

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_tokens=10000,
            )

            if response.choices:
                break

            last_error = (
                f"OpenRouter returned no choices. "
                f"Response ID: {getattr(response, 'id', None)}"
            )

        except Exception as exc:
            last_error = str(exc)

        if attempt < 2:
            time.sleep(2 * (attempt + 1))

    else:
        raise RuntimeError(
            "Patch generation failed after 3 attempts.\n"
            f"Last error: {last_error}"
        )

    message = response.choices[0].message

    if not message or not message.content:
        raise RuntimeError("LLM returned empty patch content.")

    content = message.content.strip()

    if content.startswith("```json"):
        content = content[7:].strip()
    elif content.startswith("```"):
        content = content[3:].strip()

    if content.endswith("```"):
        content = content[:-3].strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "LLM returned invalid JSON.\n\n"
            f"Raw response:\n{content}"
        ) from exc

    changes = []

    for item in data.get("changes", []):

        operation = item.get("operation", "modify").lower()
        path = item["path"]
        explanation = item["explanation"]
        new_content = item.get("content")

        if operation not in {"modify", "create", "delete"}:
            raise RuntimeError(
                f"Unsupported file operation: {operation}"
            )

        if path.startswith("/") or ".." in path.split("/"):
            raise RuntimeError(
                f"Unsafe file path returned by LLM: {path}"
            )

        if operation == "modify":

            if path not in file_contents:
                raise RuntimeError(
                    f"LLM attempted to modify an uninspected file: {path}"
                )

            if new_content is None:
                raise RuntimeError(
                    f"Modified file has no content: {path}"
                )

            old_lines = file_contents[path].splitlines(
                keepends=True
            )
            new_lines = new_content.splitlines(
                keepends=True
            )

            patch = "".join(
                difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"a/{path}",
                    tofile=f"b/{path}",
                )
            )

        elif operation == "create":

            if new_content is None:
                raise RuntimeError(
                    f"Created file has no content: {path}"
                )

            new_lines = new_content.splitlines(
                keepends=True
            )

            patch = "".join(
                difflib.unified_diff(
                    [],
                    new_lines,
                    fromfile="/dev/null",
                    tofile=f"b/{path}",
                )
            )

        else:
            patch = "".join(
                difflib.unified_diff(
                    file_contents.get(path, "").splitlines(
                        keepends=True
                    ),
                    [],
                    fromfile=f"a/{path}",
                    tofile="/dev/null",
                )
            )

        changes.append(
            FileChange(
                operation=operation,
                path=path,
                explanation=explanation,
                patch=patch,
                content=new_content,
            )
        )

    if not changes:
        raise RuntimeError("LLM returned no file changes.")

    return PatchResult(
        summary=data.get(
            "summary",
            "Proposed code changes generated.",
        ),
        changes=changes,
    )