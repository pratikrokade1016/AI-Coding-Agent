from fastapi import FastAPI
from app.routes.users import router as users_router

app = FastAPI(title="Sample User API")

app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "Sample API"}
