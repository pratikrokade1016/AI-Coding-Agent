from pathlib import Path

import streamlit as st

from agent.planner import create_plan
from agent.patcher import generate_patch
from agent.applier import apply_file_change
from agent.validator import run_tests
from tools.filesystem import list_files, read_file


BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_PROJECT = BASE_DIR / "sample-project"


st.set_page_config(
    page_title="AI Coding Agent",
    page_icon="🤖",
    layout="wide",
)

if "plan" not in st.session_state:
    st.session_state["plan"] = None

if "file_contents" not in st.session_state:
    st.session_state["file_contents"] = {}

if "patch_result" not in st.session_state:
    st.session_state["patch_result"] = None

st.title("🤖 AI Coding Agent")
st.caption("Milestone 2 — task understanding, relevant-file selection and planning")


@st.cache_data
def inspect_codebase():
    files = list_files(SAMPLE_PROJECT)

    result = []

    for file_path in files:
        relative_path = str(Path(file_path).relative_to(SAMPLE_PROJECT))

        try:
            content = read_file(file_path, workspace=SAMPLE_PROJECT)
            result.append((relative_path, content))
        except UnicodeDecodeError:
            # Ignore binary/non-text files in this initial version.
            continue

    return result


st.subheader("1. Codebase")

try:
    codebase = inspect_codebase()
except Exception as exc:
    st.error(f"Could not inspect the sample project: {exc}")
    st.stop()

st.success(f"Discovered {len(codebase)} readable files.")

with st.expander("View codebase files"):
    for relative_path, _ in codebase:
        st.write(f"• `{relative_path}`")


st.subheader("2. Coding task")

task = st.text_area(
    "Describe what the coding agent should do",
    height=120,
    placeholder=(
        "Example: Add input validation to the user registration "
        "API and write tests for invalid input."
    ),
)


if st.button("🧠 Analyze Task & Create Plan", type="primary"):
    if not task.strip():
        st.warning("Please enter a coding task.")
        st.stop()

    with st.status("Agent is analyzing the codebase...", expanded=True) as status:
        st.write("✓ Task received")
        st.write("✓ Codebase inspected")
        st.write("→ Asking the LLM to identify relevant files and create a plan...")

        try:
            result = create_plan(task, codebase)
            # Save the plan because Streamlit reruns the script
            st.session_state["plan"] = result
        except Exception as exc:
            status.update(label="Agent failed", state="error")
            st.error(str(exc))
            st.stop()

        status.update(label="Plan created", state="complete")

    st.subheader("3. Task Understanding")
    st.write(result.task_summary)

    st.subheader("4. Relevant Files")

    for item in result.relevant_files:
        st.markdown(f"**`{item.path}`**")
        st.caption(item.reason)

    st.subheader("5. Implementation Plan")

    for index, step in enumerate(result.plan, start=1):
        st.write(f"**{index}.** {step}")

    if result.assumptions:
        st.subheader("6. Assumptions")

        for assumption in result.assumptions:
            st.write(f"• {assumption}")

    st.success(
        "Planning milestone complete. "
        "The next milestone will generate and apply controlled code patches."
    )

# ============================================================
# 7. SOURCE CODE INSPECTION
# ============================================================

st.divider()

st.subheader("7. Source Code Inspection")

saved_plan = st.session_state.get("plan")

if saved_plan is not None:

    selected_files = [
        item.path
        for item in saved_plan.relevant_files
    ]

    file_contents = st.session_state.get(
        "file_contents",
        {}
    )

    if not file_contents:

        for relative_path in selected_files:

            file_path = SAMPLE_PROJECT / relative_path

            content = read_file(
                file_path,
                workspace=SAMPLE_PROJECT,
            )

            file_contents[relative_path] = content

        st.session_state["file_contents"] = file_contents

    # Display inspected files
    if file_contents:

        st.success(
            f"Inspected {len(file_contents)} relevant file(s)."
        )

        for path, content in file_contents.items():

            with st.expander(f"📄 {path}"):

                st.code(
                    content,
                    language="python"
                )

    else:

        st.warning(
            "No relevant source files could be inspected."
        )

# ============================================================
# 8. PROPOSED CODE CHANGES
# ============================================================

st.divider()

st.subheader("8. Proposed Code Changes")

saved_plan = st.session_state.get("plan")

file_contents = st.session_state.get(
    "file_contents",
    {}
)

if saved_plan is None:

    st.info(
        "Create the implementation plan first."
    )

elif not file_contents:

    st.warning(
        "No relevant source files have been inspected yet."
    )

else:

    st.write(
        "The agent has inspected the relevant source files. "
        "You can now generate a proposed code patch."
    )

    if st.button(
        "🛠️ Generate Proposed Patch",
        type="primary",
    ):

        plan_text = "\n".join(
            f"{index + 1}. {step}"
            for index, step in enumerate(
                saved_plan.plan
            )
        )

        with st.status(
            "Agent is generating the proposed patch...",
            expanded=True
        ) as status:

            st.write("✓ Task understood")
            st.write("✓ Relevant files identified")
            st.write("✓ Source files inspected")
            st.write(
                "→ Asking Nemotron to generate code changes..."
            )

            try:

                patch_result = generate_patch(
                    task=task,
                    plan=plan_text,
                    file_contents=file_contents,
                )

                st.session_state["patch_result"] = patch_result

            except Exception as exc:

                status.update(
                    label="Patch generation failed",
                    state="error"
                )

                st.error(str(exc))
                st.stop()

            status.update(
                label="Proposed patch generated",
                state="complete"
            )


# ============================================================
# DISPLAY PATCH RESULT
# ============================================================

patch_result = st.session_state.get(
    "patch_result"
)

if patch_result:

    st.success(
        "Proposed patch generated successfully."
    )

    st.markdown("### Summary")

    st.write(
        patch_result.summary
    )

    st.markdown("### Changed Files")

    for change in patch_result.changes:

        operation_label = change.operation.upper()

        st.markdown(
            f"#### 📄 `{change.path}` — `{operation_label}`"
        )

        st.markdown(
            f"**Why this changes:** "
            f"{change.explanation}"
        )

        st.markdown("**Proposed Diff:**")

        st.code(
            change.patch,
            language="diff"
        )

        st.divider()

st.subheader("9. Apply Changes")

st.warning(
    "This will modify the sample project using the "
    "AI-generated patch."
)

if st.button("✅ Apply Proposed Patch", type="primary"):
    try:
        all_changed_files = []

        for change in patch_result.changes:

            changed = apply_file_change(
                workspace=SAMPLE_PROJECT,
                operation=change.operation,
                path=change.path,
                content=change.content,
            )

            all_changed_files.append(changed)

        st.session_state["applied_files"] = all_changed_files

        st.success(
            f"Successfully applied {len(all_changed_files)} file change(s)."
        )

        for file_path in all_changed_files:
            st.write(f"• `{file_path}`")

    except Exception as exc:
        st.error(f"File change failed: {exc}")


# ============================================================
# 10. VALIDATION
# ============================================================

st.divider()

st.subheader("10. Validation")

applied_files = st.session_state.get(
    "applied_files",
    []
)

if not applied_files:

    st.info(
        "Apply the proposed patch first."
    )

else:

    st.success(
        f"Changed {len(applied_files)} file(s)."
    )

    for file_path in applied_files:

        st.write(
            f"• `{file_path}`"
        )

    if st.button(
        "🧪 Run Tests",
        type="primary",
    ):

        with st.spinner(
            "Running project tests..."
        ):

            passed, output = run_tests(
                SAMPLE_PROJECT
            )

        if passed:

            st.success(
                "All tests passed."
            )

        else:

            st.error(
                "Tests failed."
            )

        st.code(
            output,
            language="text"
        )