from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/")
def create_user(username: str, email: str):
    return {
        "username": username,
        "email": email,
        "message": "User created successfully",
    }


@router.get("/")
def get_users():
    return [
        {
            "username": "demo",
            "email": "demo@example.com",
        }
    ]