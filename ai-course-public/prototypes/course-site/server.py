"""
Course Delivery Site - FastAPI backend
Run: uvicorn server:app --reload
Then open http://localhost:8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json
import hashlib
import secrets
from datetime import datetime


app = FastAPI(title="AIForBiz Course Platform")

# Static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Data files
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)
USERS_FILE = data_dir / "users.json"
PROGRESS_FILE = data_dir / "progress.json"

# --- Course content (5 modules, 12 lessons) ---
COURSE = {
    "title": "AI for Small Business Owners",
    "modules": [
        {
            "id": 1,
            "title": "Getting Started with AI",
            "lessons": [
                {"id": "1.1", "title": "Welcome & What You'll Build", "duration": 5, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
                {"id": "1.2", "title": "Your First AI Win in 15 Minutes", "duration": 10, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
            ],
        },
        {
            "id": 2,
            "title": "AI for Writing & Content",
            "lessons": [
                {"id": "2.1", "title": "Master ChatGPT for Business Writing", "duration": 8, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
                {"id": "2.2", "title": "Create 30 Days of Content in 1 Hour", "duration": 12, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
                {"id": "2.3", "title": "Write Better Emails with Claude", "duration": 7, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
            ],
        },
        {
            "id": 3,
            "title": "AI for Customer Service",
            "lessons": [
                {"id": "3.1", "title": "Build an Auto-Reply System", "duration": 10, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
                {"id": "3.2", "title": "Create a FAQ Bot (No Code)", "duration": 9, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
            ],
        },
        {
            "id": 4,
            "title": "AI for Marketing",
            "lessons": [
                {"id": "4.1", "title": "Email Campaigns That Convert", "duration": 11, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
                {"id": "4.2", "title": "Social Media on Autopilot", "duration": 10, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
            ],
        },
        {
            "id": 5,
            "title": "Your 7-Day Action Plan",
            "lessons": [
                {"id": "5.1", "title": "Day-by-Day Implementation", "duration": 15, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
                {"id": "5.2", "title": "Measuring Your Wins", "duration": 8, "video": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
            ],
        },
    ],
}


# --- Models ---
class Signup(BaseModel):
    email: str
    name: str
    course: str = "main"


class ProgressUpdate(BaseModel):
    email: str
    lesson_id: str
    completed: bool


# --- Helpers ---
def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def get_user(email: str):
    users = load_json(USERS_FILE, [])
    for u in users:
        if u["email"] == email:
            return u
    return None


# --- Routes ---
@app.get("/")
def home():
    return FileResponse(static_dir / "index.html")


@app.get("/api/course")
def get_course():
    """Return full course structure"""
    return COURSE


@app.get("/api/course/stats")
def get_stats():
    """Return course stats"""
    total_lessons = sum(len(m["lessons"]) for m in COURSE["modules"])
    total_duration = sum(
        l["duration"] for m in COURSE["modules"] for l in m["lessons"]
    )
    return {
        "modules": len(COURSE["modules"]),
        "lessons": total_lessons,
        "total_minutes": total_duration,
        "total_hours": round(total_duration / 60, 1),
    }


@app.post("/api/signup")
def signup(data: Signup):
    """Create user account"""
    users = load_json(USERS_FILE, [])
    if get_user(data.email):
        raise HTTPException(400, "Email already registered")

    user = {
        "email": data.email,
        "name": data.name,
        "course": data.course,
        "signup_date": datetime.now().isoformat(),
        "access_token": secrets.token_urlsafe(16),
    }
    users.append(user)
    save_json(USERS_FILE, users)

    return {"message": "Welcome!", "user": user}


@app.get("/api/progress/{email}")
def get_progress(email: str):
    """Get lesson completion for a user"""
    if not get_user(email):
        raise HTTPException(404, "User not found")
    progress = load_json(PROGRESS_FILE, {})
    return progress.get(email, {})


@app.post("/api/progress")
def update_progress(data: ProgressUpdate):
    """Mark lesson complete/incomplete"""
    if not get_user(data.email):
        raise HTTPException(404, "User not found")

    progress = load_json(PROGRESS_FILE, {})
    user_progress = progress.setdefault(data.email, {})
    user_progress[data.lesson_id] = {
        "completed": data.completed,
        "timestamp": datetime.now().isoformat(),
    }
    save_json(PROGRESS_FILE, progress)

    # Calculate completion percentage
    total_lessons = sum(len(m["lessons"]) for m in COURSE["modules"])
    completed = sum(1 for v in user_progress.values() if v.get("completed"))
    pct = round((completed / total_lessons) * 100, 1)

    return {"completion_pct": pct, "completed_lessons": completed, "total_lessons": total_lessons}


@app.get("/api/leaderboard")
def leaderboard():
    """Show top students by completion"""
    users = load_json(USERS_FILE, [])
    progress = load_json(PROGRESS_FILE, {})
    total_lessons = sum(len(m["lessons"]) for m in COURSE["modules"])

    board = []
    for u in users:
        up = progress.get(u["email"], {})
        completed = sum(1 for v in up.values() if v.get("completed"))
        pct = round((completed / total_lessons) * 100, 1) if total_lessons else 0
        board.append({"name": u["name"], "email": u["email"], "completion": pct, "completed_lessons": completed})

    board.sort(key=lambda x: x["completion"], reverse=True)
    return board[:10]


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print(" AIForBiz Course Platform ".center(50, "="))
    print("=" * 50)
    print("Open: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
