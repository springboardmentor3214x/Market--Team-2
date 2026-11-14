from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.user import UserRegister, UserLogin, UserResponse
from backend.app.schemas.token import Token
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.core.deps import get_current_user
from backend.app.crud.crud_user import get_user_by_email, create_user
from backend.app.models.user import User

router = APIRouter(tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """
    1. User Registration:
       - Validates email and password
       - Hashes the password using bcrypt
       - Stores user in PostgreSQL database
    """
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Securely hash the password before database insertion
    hashed_pwd = get_password_hash(user_in.password)

    new_user = create_user(
        db=db,
        email=user_in.email,
        password_hash=hashed_pwd,
        preferences=user_in.preferences
    )

    return {
        "message": "Registration successful!",
        "user_id": str(new_user.user_id),
        "email": new_user.email
    }


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    2. User Login and JWT Authentication:
       - Checks whether user exists
       - Verifies password against stored bcrypt hash
       - Generates and returns a signed JWT access token
    """
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT access token with user_id as subject
    access_token = create_access_token(subject=str(user.user_id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user.user_id),
            "email": user.email,
            "preferences": user.preferences
        }
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile and preferences.
    """
    return current_user
