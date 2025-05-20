from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import json
import os
from openai import OpenAI

# Initialize FastAPI app
app = FastAPI(title="AI Job Search API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "your-secret-key-for-development-only"  # In production, use a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    skills: List[str] = []
    experience: List[dict] = []
    education: List[dict] = []
    preferences: dict = {}

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    preferences: Optional[dict] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Job(BaseModel):
    id: Optional[int] = None
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    salary_range: Optional[str] = None
    posted_date: datetime
    is_remote: bool = False
    job_type: str  # full-time, part-time, contract, etc.

class JobRecommendation(BaseModel):
    job_id: int
    match_score: float
    match_reasons: List[str]

# Mock database
users_db = {}
jobs_db = {}

# Load sample data
def load_sample_data():
    # Sample users
    users_db[1] = User(
        id=1,
        username="johndoe",
        email="john@example.com",
        hashed_password=pwd_context.hash("password123"),
        full_name="John Doe",
        skills=["Python", "React", "JavaScript", "Machine Learning"],
        experience=[
            {"title": "Software Engineer", "company": "Tech Corp", "years": 3},
            {"title": "Junior Developer", "company": "Startup Inc", "years": 2}
        ],
        education=[
            {"degree": "BS Computer Science", "institution": "Tech University", "year": 2018}
        ],
        preferences={"remote": True, "min_salary": 80000}
    )
    
    # Sample jobs
    current_date = datetime.now()
    
    for i in range(1, 11):
        remote = i % 3 == 0
        job_type = "full-time" if i % 4 != 0 else "contract"
        
        jobs_db[i] = Job(
            id=i,
            title=f"Software Engineer {i}",
            company=f"Company {i}",
            location="Remote" if remote else f"City {i}",
            description=f"This is a job description for position {i}. We are looking for talented engineers.",
            requirements=["Python", "JavaScript", "React"] if i % 2 == 0 else ["Java", "Spring", "SQL"],
            salary_range=f"${70000 + i*5000}-${90000 + i*5000}",
            posted_date=current_date - timedelta(days=i),
            is_remote=remote,
            job_type=job_type
        )

# Security functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    for user_id, user in users_db.items():
        if user.username == username:
            return user
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# AI recommendation function
def get_ai_job_recommendations(user: User, jobs: List[Job], top_n: int = 5):
    # In a real application, you would use the OpenAI API here
    # For this demo, we'll use a simple matching algorithm
    
    # Mock AI recommendation logic
    recommendations = []
    
    for job_id, job in jobs_db.items():
        # Calculate a simple match score based on skills
        user_skills = set(user.skills)
        job_requirements = set(job.requirements)
        
        common_skills = user_skills.intersection(job_requirements)
        match_score = len(common_skills) / max(len(job_requirements), 1)
        
        # Add remote preference
        if user.preferences.get("remote", False) and job.is_remote:
            match_score += 0.2
        
        # Create match reasons
        match_reasons = []
        if common_skills:
            match_reasons.append(f"You have {len(common_skills)} required skills: {', '.join(common_skills)}")
        
        if user.preferences.get("remote", False) and job.is_remote:
            match_reasons.append("This job is remote, matching your preference")
            
        # Only include jobs with some match
        if match_score > 0:
            recommendations.append(
                JobRecommendation(
                    job_id=job_id,
                    match_score=match_score,
                    match_reasons=match_reasons
                )
            )
    
    # Sort by match score and take top_n
    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    return recommendations[:top_n]

# Routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    # Check if username already exists
    if get_user(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    user_id = len(users_db) + 1
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        id=user_id,
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    
    users_db[user_id] = db_user
    return db_user

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.put("/users/me", response_model=User)
async def update_user(user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    # Update user fields if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.skills is not None:
        current_user.skills = user_update.skills
    if user_update.experience is not None:
        current_user.experience = user_update.experience
    if user_update.education is not None:
        current_user.education = user_update.education
    if user_update.preferences is not None:
        current_user.preferences = user_update.preferences
    
    # Update in the database
    users_db[current_user.id] = current_user
    
    return current_user

@app.get("/jobs/", response_model=List[Job])
async def get_jobs():
    return list(jobs_db.values())

@app.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: int):
    if job_id not in jobs_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return jobs_db[job_id]

@app.get("/recommendations/", response_model=List[JobRecommendation])
async def get_recommendations(current_user: User = Depends(get_current_user)):
    recommendations = get_ai_job_recommendations(current_user, list(jobs_db.values()))
    return recommendations

@app.get("/")
async def root():
    return {"message": "Welcome to AI Job Search API"}

# Initialize sample data
load_sample_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)