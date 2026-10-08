from app.agent.planner import create_plan

files = [
    "app/__init__.py",
    "app/main.py",
    "app/routes/__init__.py",
    "app/routes/users.py",
    "tests/test_users.py",
    "requirements.txt",
]

task = "Add input validation to the user registration API and write tests for invalid input."

print("Calling planner...")

result = create_plan(task, files)

print("\nSUCCESS\n")
print("Task:", result.task_summary)

print("\nRelevant files:")
for item in result.relevant_files:
    print("-", item.path, "|", item.reason)

print("\nPlan:")
for step in result.plan:
    print("-", step)

print("\nAssumptions:")
for assumption in result.assumptions:
    print("-", assumption)