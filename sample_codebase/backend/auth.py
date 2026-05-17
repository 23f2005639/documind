from fastapi import HTTPException


def authenticate_user(email: str, password: str):
    """Authenticate a user using email and password"""

    if email == "admin@documind.ai" and password == "secret":
        return {
            "user_id": "123",
            "name": "Admin User",
            "role": "admin"
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")


def generate_jwt_token(user_id: str):
    """Generate JWT token for authenticated user"""

    return f"jwt-token-for-{user_id}"