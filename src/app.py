"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""


from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
import os
from pathlib import Path


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent, "static")), name="static")

# --- Database setup ---
DATABASE_URL = "sqlite:///" + str(current_dir / "activities.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    schedule = Column(String)
    max_participants = Column(Integer)
    participants = relationship("Participant", back_populates="activity", cascade="all, delete-orphan")

class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    activity = relationship("Activity", back_populates="participants")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)

# --- Initial data population (if empty) ---
def init_db():
    db = SessionLocal()
    if db.query(Activity).count() == 0:
        initial_activities = [
            {"name": "Chess Club", "description": "Learn strategies and compete in chess tournaments", "schedule": "Fridays, 3:30 PM - 5:00 PM", "max_participants": 12, "participants": ["michael@mergington.edu", "daniel@mergington.edu"]},
            {"name": "Programming Class", "description": "Learn programming fundamentals and build software projects", "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", "max_participants": 20, "participants": ["emma@mergington.edu", "sophia@mergington.edu"]},
            {"name": "Gym Class", "description": "Physical education and sports activities", "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", "max_participants": 30, "participants": ["john@mergington.edu", "olivia@mergington.edu"]},
            {"name": "Soccer Team", "description": "Join the school soccer team and compete in matches", "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", "max_participants": 22, "participants": ["liam@mergington.edu", "noah@mergington.edu"]},
            {"name": "Basketball Team", "description": "Practice and play basketball with the school team", "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM", "max_participants": 15, "participants": ["ava@mergington.edu", "mia@mergington.edu"]},
            {"name": "Art Club", "description": "Explore your creativity through painting and drawing", "schedule": "Thursdays, 3:30 PM - 5:00 PM", "max_participants": 15, "participants": ["amelia@mergington.edu", "harper@mergington.edu"]},
            {"name": "Drama Club", "description": "Act, direct, and produce plays and performances", "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM", "max_participants": 20, "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]},
            {"name": "Math Club", "description": "Solve challenging problems and participate in math competitions", "schedule": "Tuesdays, 3:30 PM - 4:30 PM", "max_participants": 10, "participants": ["james@mergington.edu", "benjamin@mergington.edu"]},
            {"name": "Debate Team", "description": "Develop public speaking and argumentation skills", "schedule": "Fridays, 4:00 PM - 5:30 PM", "max_participants": 12, "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]},
        ]
        for act in initial_activities:
            activity = Activity(
                name=act["name"],
                description=act["description"],
                schedule=act["schedule"],
                max_participants=act["max_participants"]
            )
            db.add(activity)
            db.flush()  # get activity.id
            for email in act["participants"]:
                db.add(Participant(email=email, activity=activity))
        db.commit()
    db.close()

init_db()





@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")



@app.get("/activities")
def get_activities(db: Session = Depends(get_db)):
    result = {}
    for activity in db.query(Activity).all():
        result[activity.name] = {
            "description": activity.description,
            "schedule": activity.schedule,
            "max_participants": activity.max_participants,
            "participants": [p.email for p in activity.participants]
        }
    return result



@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, db: Session = Depends(get_db)):
    """Sign up a student for an activity"""
    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if email in [p.email for p in activity.participants]:
        raise HTTPException(status_code=400, detail="Student is already signed up")
    if len(activity.participants) >= activity.max_participants:
        raise HTTPException(status_code=400, detail="Activity is full")
    participant = Participant(email=email, activity=activity)
    db.add(participant)
    db.commit()
    return {"message": f"Signed up {email} for {activity_name}"}



@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, db: Session = Depends(get_db)):
    """Unregister a student from an activity"""
    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    participant = db.query(Participant).filter(Participant.activity_id == activity.id, Participant.email == email).first()
    if not participant:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")
    db.delete(participant)
    db.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
