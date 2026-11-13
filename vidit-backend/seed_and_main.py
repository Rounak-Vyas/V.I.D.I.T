from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime

# Replace with your local Postgres password OR your Supabase URI
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/vidit_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# --- MODELS ---
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTO-SEED INITIAL DATA ON STARTUP ---
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
        # Seeding Team IoTronics + Wokwi RFID UIDs
        students = [
            Student(uid="NB25ECE022", usn="NB25ECE022", name="Ananya Manjunath"),
            Student(uid="1NT24EC019", usn="1NT24EC019", name="Amogh D Pinglay"),
            Student(uid="NB25RAI034", usn="NB25RAI034", name="Meher Chaitanya"),
            Student(uid="NB25ECE170", usn="NB25ECE170", name="Shreya Fouzdar"),
            Student(uid="1NT23EE045", usn="1NT23EE045", name="Rounak Vyas"),
            # Default Wokwi MFRC522 simulated card UID (update if yours prints a different hex)
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