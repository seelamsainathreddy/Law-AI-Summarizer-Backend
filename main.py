# backend/main.py

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import UserIn, UserOut, Token
from auth import hash_password, verify_password, create_access_token
from jose import JWTError, jwt
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from summarizer import summarize_document
from fastapi import Security

user_summaries = {}
fake_users_db = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()
# Allow frontend requests (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/summarize")
async def summarize(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    # Get user email from token
    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        email = payload.get("sub")
        if email is None or email not in fake_users_db:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    file_bytes = await file.read()
    result = summarize_document(file_bytes)

    # Save summary for user
    if email not in user_summaries:
        user_summaries[email] = []
    user_summaries[email].append(result)

    return result

@app.post("/register", response_model=UserOut)
def register(user: UserIn):
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = hash_password(user.password)
    fake_users_db[user.email] = {"email": user.email, "hashed_password": hashed}
    return {"email": user.email}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me", response_model=UserOut)
def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        email = payload.get("sub")
        if email is None or email not in fake_users_db:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


