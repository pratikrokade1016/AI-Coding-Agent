from app.agent.patcher import generate_patch


task = (
    "Add input validation to the user registration API "
    "and write tests for invalid input."
)

plan = """
1. Create a Pydantic model UserCreate with validation for username
   and email.
2. Update create_user to accept UserCreate as the request body.
3. Add tests for invalid email, empty username, username length,
   and missing fields.
4. Verify the existing valid input test still passes.
"""

file_contents = {
    "app/routes/users.py": """
from fastapi import APIRouter

router = APIRouter()

users = []


@router.post("/users/")
def create_user(username: str, email: str):
    user = {
        "username": username,
        "email": email,
    }

    users.append(user)

    return user


@router.get("/users/")
def get_users():
    return users
""",

    "tests/test_users.py": """
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_user():
    response = client.post(
        "/users/",
        params={
            "username": "john",
            "email": "john@example.com",
        },
    )

    assert response.status_code == 200
"""
}


print("Calling patch generator...\n")

result = generate_patch(
    task=task,
    plan=plan,
    file_contents=file_contents,
)

print("SUCCESS\n")

print("SUMMARY:")
print(result.summary)

print("\nCHANGES:")

for change in result.changes:

    print("\nFILE:", change.path)

    print("\nEXPLANATION:")
    print(change.explanation)

    print("\nPATCH:")
    print(change.patch)