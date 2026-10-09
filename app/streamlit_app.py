
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
    page_title="DevAgent | AI Coding Workspace",
    page_icon="D",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULTS = {
    "plan": None,
    "file_contents": {},
    "patch_result": None,
    "applied_files": [],
    "test_result": None,
    "active_task": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    :root {
        --accent: #8b7cff;
        --accent-soft: rgba(139, 124, 255, 0.13);
        --panel: var(--secondary-background-color);
        --border: rgba(128, 128, 128, 0.22);
    }

    .stApp {
        background: var(--background-color);
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 5px;
    }

    .brand-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 13px;
        background: linear-gradient(135deg, #a397ff, #6954dc);
        color: white;
        font-size: 22px;
        font-weight: 800;
    }

    .brand-title {
        font-size: 21px;
        font-weight: 750;
        letter-spacing: -0.8px;
    }

    .muted {
        color: var(--text-color);
        opacity: 0.63;
        font-size: 0.84rem;
    }

    .hero {
        padding: 24px 0 15px 0;
    }

    .eyebrow {
        color: #a397ff;
        font-size: 0.75rem;
        font-weight: 750;
        letter-spacing: 1.8px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .hero h1 {
        font-size: clamp(2rem, 4vw, 3rem);
        font-weight: 780;
        letter-spacing: -1.7px;
        line-height: 1.13;
        margin: 0 0 12px 0;
    }

    .hero p {
        font-size: 1rem;
        opacity: 0.72;
        line-height: 1.7;
        max-width: 700px;
    }

    .section-heading {
        font-size: 1.1rem;
        font-weight: 720;
        letter-spacing: -0.3px;
        margin-bottom: 5px;
    }

    .step-label {
        font-size: 0.79rem;
        font-weight: 650;
        line-height: 1.4;
    }

    .step-card {
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 13px 10px;
        min-height: 76px;
        background: var(--secondary-background-color);
    }

    .step-number {
        color: #a397ff;
        font-size: 0.75rem;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .file-card {
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 13px 15px;
        margin: 8px 0;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #39c98a;
        margin-right: 7px;
    }

    .stButton > button {
        border-radius: 10px;
        min-height: 43px;
        font-weight: 650;
        transition: border-color 0.15s ease;
    }

    .stButton > button[kind="primary"] {
        border: 1px solid #8b7cff;
    }

    div[data-testid="stTextArea"] textarea {
        border-radius: 12px;
        line-height: 1.6;
    }

    div[data-testid="stTabs"] button {
        font-weight: 650;
    }

    div[data-testid="stExpander"] {
        border-radius: 10px;
        border-color: var(--border);
    }

    .footer-note {
        font-size: 0.78rem;
        opacity: 0.55;
        text-align: center;
        padding: 25px 0 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# FILE DISCOVERY
# --------------------------------------------------

@st.cache_data
def inspect_codebase():
    files = list_files(SAMPLE_PROJECT)
    result = []

    for file_path in files:
        relative_path = str(
            Path(file_path).relative_to(SAMPLE_PROJECT)
        )

        try:
            content = read_file(
                file_path,
                workspace=SAMPLE_PROJECT,
            )
            result.append((relative_path, content))
        except (UnicodeDecodeError, OSError):
            continue

    return result


try:
    codebase = inspect_codebase()
except Exception as exc:
    st.error(f"Could not inspect the sample project: {exc}")
    st.stop()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">D</div>
            <div>
                <div class="brand-title">DevAgent</div>
                <div class="muted">AI Coding Workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption("WORKSPACE")

    st.markdown("**Sample Project**")
    st.caption("Python · FastAPI · Pytest")

    st.markdown(
        f"**{len(codebase)}** readable project files"
    )

    with st.expander("Browse project files"):
        for path, _ in codebase:
            st.code(path, language="text")

    st.divider()
    st.caption("AGENT PIPELINE")

    stages = [
        ("01", "Understand task"),
        ("02", "Inspect files"),
        ("03", "Review changes"),
        ("04", "Apply changes"),
        ("05", "Run tests"),
    ]

    for number, label in stages:
        st.markdown(
            f"""
            <div style="display:flex; gap:11px;
                        align-items:center; padding:8px 0;">
                <span style="color:#a397ff; font-weight:750;
                             font-size:0.8rem;">{number}</span>
                <span style="font-size:0.88rem;">{label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown(
        '<span class="status-dot"></span> Workspace ready',
        unsafe_allow_html=True,
    )
    st.caption("Model requests use your OpenRouter configuration.")


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">AI Developer Tools / Coding Agent</div>
        <h1>Build something<br>better with AI.</h1>
        <p>
            Describe a coding task. DevAgent will explore your codebase,
            create an implementation plan, propose changes, and validate
            the result with automated tests.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# TASK COMPOSER
# --------------------------------------------------

st.markdown('<div class="section-heading">What should I work on?</div>',
            unsafe_allow_html=True)
st.caption("Describe the change you want in plain English.")

task = st.text_area(
    "Coding task",
    key="task_input",
    height=125,
    label_visibility="collapsed",
    placeholder=(
        "Example: Add input validation to the user registration "
        "API and write tests for invalid input scenarios..."
    ),
)

col_hint, col_run = st.columns([3, 1])

with col_hint:
    st.caption("Tip: Be specific about expected behavior and edge cases.")

with col_run:
    analyze_clicked = st.button(
        "Analyze task  →",
        type="primary",
        use_container_width=True,
        key="analyze_task",
    )


# --------------------------------------------------
# PLAN GENERATION
# --------------------------------------------------

if analyze_clicked:
    if not task.strip():
        st.warning("Enter a coding task before running the agent.")
    else:
        # Clear the previous task's state before starting a new one.
        for key in [
            "plan",
            "file_contents",
            "patch_result",
            "applied_files",
            "test_result",
        ]:
            st.session_state[key] = (
                {} if key == "file_contents" else
                [] if key == "applied_files" else
                None
            )

        st.session_state["active_task"] = task.strip()

        with st.status(
            "Analyzing your task...",
            expanded=True,
        ) as status:
            st.write("Task received")
            st.write("Project file list loaded")
            st.write("Identifying relevant files and planning changes")

            try:
                result = create_plan(
                    task.strip(),
                    codebase,
                )

                st.session_state["plan"] = result
                status.update(
                    label="Implementation plan ready",
                    state="complete",
                    expanded=False,
                )

            except Exception as exc:
                status.update(
                    label="Planning failed",
                    state="error",
                    expanded=True,
                )
                st.error(str(exc))


# --------------------------------------------------
# WORKFLOW PROGRESS
# --------------------------------------------------

saved_plan = st.session_state.get("plan")
saved_patch = st.session_state.get("patch_result")
applied_files = st.session_state.get("applied_files", [])
test_result = st.session_state.get("test_result")

st.divider()
st.markdown("### Agent workspace")

progress_columns = st.columns(5)

progress_states = [
    saved_plan is not None,
    bool(st.session_state.get("file_contents")),
    saved_patch is not None,
    bool(applied_files),
    test_result is not None,
]

progress_labels = [
    "Understand",
    "Inspect",
    "Review",
    "Apply",
    "Validate",
]

for index, column in enumerate(progress_columns):
    complete = progress_states[index]

    with column:
        st.markdown(
            f"""
            <div class="step-card">
                <div class="step-number">
                    {"✓ COMPLETE" if complete else f"STEP {index + 1:02d}"}
                </div>
                <div class="step-label">{progress_labels[index]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# WORKSPACE TABS
# --------------------------------------------------

plan_tab, review_tab, validation_tab = st.tabs(
    ["Plan & Files", "Code Review", "Validation"]
)


# --------------------------------------------------
# PLAN & SOURCE INSPECTION
# --------------------------------------------------

with plan_tab:
    if saved_plan is None:
        st.info("Your implementation plan will appear here after analysis.")
    else:
        st.markdown("#### Task understanding")
        st.write(saved_plan.task_summary)

        st.divider()
        st.markdown("#### Relevant files")

        for item in saved_plan.relevant_files:
            with st.container(border=True):
                st.markdown(f"**`{item.path}`**")
                st.caption(item.reason)

        st.divider()
        st.markdown("#### Implementation plan")

        for index, step in enumerate(saved_plan.plan, start=1):
            st.markdown(f"**{index}.** {step}")

        if saved_plan.assumptions:
            with st.expander("Assumptions"):
                for assumption in saved_plan.assumptions:
                    st.write(f"- {assumption}")

        # Inspect the selected files once per task.
        file_contents = st.session_state.get("file_contents", {})

        if not file_contents:
            inspected = {}

            for item in saved_plan.relevant_files:
                try:
                    inspected[item.path] = read_file(
                        SAMPLE_PROJECT / item.path,
                        workspace=SAMPLE_PROJECT,
                    )
                except Exception as exc:
                    st.error(f"Could not inspect {item.path}: {exc}")

            st.session_state["file_contents"] = inspected
            file_contents = inspected

        st.divider()
        st.markdown("#### Source code inspection")
        st.caption(f"{len(file_contents)} relevant file(s) inspected")

        for path, content in file_contents.items():
            with st.expander(path):
                suffix = Path(path).suffix.lower()
                language = {
                    ".py": "python",
                    ".js": "javascript",
                    ".ts": "typescript",
                    ".json": "json",
                    ".md": "markdown",
                    ".html": "html",
                    ".css": "css",
                    ".sql": "sql",
                }.get(suffix, "text")

                st.code(content, language=language)


# --------------------------------------------------
# CODE REVIEW AND APPLY
# --------------------------------------------------

with review_tab:
    file_contents = st.session_state.get("file_contents", {})
    saved_plan = st.session_state.get("plan")
    saved_patch = st.session_state.get("patch_result")

    if saved_plan is None:
        st.info("Analyze a task before generating code changes.")

    elif not file_contents:
        st.warning("No relevant files were inspected. Review the task and try again.")

    else:
        st.markdown("#### Proposed implementation")
        st.caption(
            "Review the generated changes before applying them to the sample project."
        )

        if st.button(
            "Generate proposed changes",
            type="primary",
            use_container_width=True,
            key="generate_patch",
        ):
            plan_text = "\n".join(
                f"{index + 1}. {step}"
                for index, step in enumerate(saved_plan.plan)
            )

            try:
                with st.spinner("Generating code changes..."):
                    patch_result = generate_patch(
                        task=st.session_state["active_task"],
                        plan=plan_text,
                        file_contents=file_contents,
                    )

                st.session_state["patch_result"] = patch_result
                st.session_state["applied_files"] = []
                st.session_state["test_result"] = None
                st.rerun()

            except Exception as exc:
                st.error(f"Patch generation failed: {exc}")

        saved_patch = st.session_state.get("patch_result")

        if saved_patch:
            st.success(saved_patch.summary)

            for change in saved_patch.changes:
                with st.container(border=True):
                    left, right = st.columns([4, 1])

                    with left:
                        st.markdown(f"**`{change.path}`**")
                        st.caption(change.explanation)

                    with right:
                        st.markdown(f"`{change.operation.upper()}`")

                    st.code(change.patch or "No textual differences.",
                            language="diff")

            st.divider()
            st.warning(
                "Applying changes will modify the sample project files."
            )

            if not st.session_state.get("applied_files"):
                if st.button(
                    "Apply changes to workspace",
                    type="primary",
                    use_container_width=True,
                    key="apply_changes",
                ):
                    try:
                        changed_files = []

                        for change in saved_patch.changes:
                            changed = apply_file_change(
                                workspace=SAMPLE_PROJECT,
                                operation=change.operation,
                                path=change.path,
                                content=change.content,
                            )
                            changed_files.append(changed)

                        st.session_state["applied_files"] = changed_files
                        st.session_state["test_result"] = None

                        st.success(
                            f"Applied {len(changed_files)} file change(s)."
                        )
                        st.rerun()

                    except Exception as exc:
                        st.error(f"Could not apply changes: {exc}")
            else:
                st.success("Changes have been applied.")
                for path in st.session_state["applied_files"]:
                    st.write(f"- `{path}`")


# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

with validation_tab:
    applied_files = st.session_state.get("applied_files", [])
    test_result = st.session_state.get("test_result")

    st.markdown("#### Automated validation")
    st.caption("Run the sample project's Pytest suite after applying changes.")

    if not applied_files:
        st.info("Apply the proposed changes before running validation.")
    else:
        st.markdown("**Changed files**")
        for path in applied_files:
            st.write(f"- `{path}`")

        if st.button(
            "Run tests",
            type="primary",
            use_container_width=True,
            key="run_tests",
        ):
            try:
                with st.spinner("Running Pytest..."):
                    passed, output = run_tests(SAMPLE_PROJECT)

                st.session_state["test_result"] = {
                    "passed": passed,
                    "output": output,
                }
                st.rerun()

            except Exception as exc:
                st.error(f"Validation could not run: {exc}")

        test_result = st.session_state.get("test_result")

        if test_result is not None:
            if test_result["passed"]:
                st.success("All tests passed.")
            else:
                st.error("Some tests failed.")

            st.code(test_result["output"] or "No test output.", language="text")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
    """
    <div class="footer-note">
        DevAgent · AI-assisted coding with reviewable changes and automated validation
    </div>
    """,
    unsafe_allow_html=True,
)
