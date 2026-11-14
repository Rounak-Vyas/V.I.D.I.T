from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

# Type your actual Supabase password inside the quotes on the password line below:
db_url = URL.create(
    drivername="postgresql+psycopg",
    username="postgres.odqlcieonaxsmgbclcxe",
    password="Logintovidit@100%",
    host="aws-1-ap-northeast-2.pooler.supabase.com",
    port=5432,
    database="postgres"
)

engine = create_engine(db_url)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# --- DATABASE TABLES ---
class Student(Base):
    __tablename__ = "students"
    uid = Column(String, primary_key=True, index=True)
    usn = Column(String)
    name = Column(String)
    is_hostellite = Column(Boolean, default=True)
    on_leave = Column(Boolean, default=False)
    current_zone = Column(String, default="OUTSIDE")

class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, index=True)
    gate_location = Column(String)
    direction = Column(String)
    method = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Facility(Base):
    __tablename__ = "facilities"
    name = Column(String, primary_key=True)
    max_capacity = Column(Integer)
    current_occupancy = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="V.I.D.I.T Prototype Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SEED INITIAL DATA ON STARTUP ---
@app.on_event("startup")
def seed_database():
    db = SessionLocal()
    if db.query(Facility).count() == 0:
        facilities = [
            Facility(name="CAMPUS_MAIN", max_capacity=3000, current_occupancy=248),
            Facility(name="MESS", max_capacity=800, current_occupancy=120),
            Facility(name="LIBRARY", max_capacity=150, current_occupancy=102),
        ]
        db.add_all(facilities)

    if db.query(Student).count() == 0:
        students = [
            Student(uid="NB25ECE022", usn="NB25ECE022", name="Ananya Manjunath"),
            Student(uid="1NT24EC019", usn="1NT24EC019", name="Amogh D Pinglay"),
            Student(uid="NB25RAI034", usn="NB25RAI034", name="Meher Chaitanya"),
            Student(uid="NB25ECE170", usn="NB25ECE170", name="Shreya Fouzdar"),
            Student(uid="1NT23EE045", usn="1NT23EE045", name="Rounak Vyas"),
            Student(uid="01020304", usn="1NT24EC019", name="Amogh (RFID Card)"),
        ]
        db.add_all(students)
    db.commit()
    db.close()

# --- API ENDPOINTS ---
class ScanPayload(BaseModel):
    uid: str
    gate_location: str
    direction: str
    method: str = "RFID"

@app.post("/api/terminal/scan")
def process_scan(payload: ScanPayload, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.uid == payload.uid).first()
    if not student or student.on_leave:
        raise HTTPException(status_code=403, detail=f"Access Denied for UID: {payload.uid}")

    facility = db.query(Facility).filter(Facility.name == payload.gate_location).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Invalid Gate Location")

    if payload.direction == "ENTRY" and student.current_zone != payload.gate_location:
        facility.current_occupancy += 1
        student.current_zone = payload.gate_location
    elif payload.direction == "EXIT" and facility.current_occupancy > 0:
        facility.current_occupancy -= 1
        student.current_zone = "CAMPUS_MAIN" if payload.gate_location != "CAMPUS_MAIN" else "OUTSIDE"

    log = AccessLog(
        uid=payload.uid,
        gate_location=payload.gate_location,
        direction=payload.direction,
        method=payload.method
    )
    db.add(log)
    db.commit()

    return {
        "status": "Access Granted",
        "student": student.name,
        "gate": facility.name,
        "live_occupancy": facility.current_occupancy,
        "available_capacity": facility.max_capacity - facility.current_occupancy
    }

@app.get("/api/com/status")
def get_occupancy_status(db: Session = Depends(get_db)):
    facilities = db.query(Facility).all()
    return [
        {
            "facility": f.name,
            "current": f.current_occupancy,
            "max": f.max_capacity,
            "available": f.max_capacity - f.current_occupancy,
            "status": "Near Full" if f.current_occupancy / f.max_capacity > 0.8 else "Available"
        }
        for f in facilities
    ]

# --- MESS INTELLIGENCE MODEL (MIM) PREDICTION ENDPOINT ---

mim_model = joblib.load("mim_model.pkl")

@app.get("/api/mim/predict")
def predict_mess_crowd(
    meal: int = 2,          # 0: Breakfast, 1: Lunch, 2: Dinner
    day_of_week: int = 4,   # 0: Mon ... 4: Fri ... 6: Sun
    exam_period: int = 1,   # 0: Normal, 1: Midsems/Exams
    is_holiday: int = 0,    # 0: No, 1: Yes
    special_meal: int = 0,  # 0: No, 1: Yes
    weather_rain: int = 1,  # 0: Clear, 1: Rain
    db: Session = Depends(get_db)
):
    # 1. Fetch live campus occupancy from Supabase
    campus = db.query(Facility).filter(Facility.name == "CAMPUS_MAIN").first()
    live_occupancy = campus.current_occupancy if campus else 250

    # 2. Run input features through the trained Random Forest model
    features = ["meal", "day_of_week", "exam_period", "is_holiday", "special_meal", "weather_rain"]
    input_df = pd.DataFrame([[meal, day_of_week, exam_period, is_holiday, special_meal, weather_rain]], columns=features)
    
    tree_preds = np.array([tree.predict(input_df.values)[0] for tree in mim_model.estimators_])
    attendance_factor = round(float(np.mean(tree_preds)), 2)
    confidence_margin = round(float(1.96 * np.std(tree_preds)), 2)

    # 3. Calculate expected turnout and preparation range
    expected_students = int(round(live_occupancy * attendance_factor))
    min_range = int(round(live_occupancy * max(0.0, attendance_factor - confidence_margin)))
    max_range = int(round(live_occupancy * min(1.0, attendance_factor + confidence_margin)))

    meal_names = {0: "Breakfast", 1: "Lunch", 2: "Dinner"}

    return {
        "meal": meal_names.get(meal, "Unknown"),
        "live_campus_occupancy": live_occupancy,
        "attendance_factor": attendance_factor,
        "confidence_margin": f"+/- {confidence_margin}",
        "expected_mess_turnout": expected_students,
        "preparation_range": f"{min_range} - {max_range}"
    }