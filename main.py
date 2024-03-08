from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
from pydantic import BaseModel
from typing import List

app = FastAPI()

Base = declarative_base()

class ContactDB(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, index=True)
    phone_number = Column(String)
    birthday = Column(Date)
    additional_data = Column(String, nullable=True)

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    additional_data: str

class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    additional_data: str

DATABASE_URL = "postgresql://myuser:1111@localhost/mydatabase"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@app.post("/contacts/", response_model=ContactResponse)
def create_contact(contact: ContactCreate):
    with SessionLocal() as db:
        db_contact = ContactDB(**contact.dict())
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
    return ContactResponse(**db_contact.__dict__)

@app.get("/contacts/", response_model=List[ContactResponse])
def read_contacts(q: str = Query(None, min_length=3)):
    with SessionLocal() as db:
        if q is None:
            return HTTPException(status_code=400, detail="Search query cannot be empty or None")
        contacts = db.query(ContactDB).filter(
            (ContactDB.first_name.contains(q)) | 
            (ContactDB.last_name.contains(q)) | 
            (ContactDB.email.contains(q))
        ).all()
    return [ContactResponse(**contact.__dict__) for contact in contacts]

@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int):
    with SessionLocal() as db:
        contact = db.query(ContactDB).get(contact_id)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse(**contact.__dict__)

@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, updated_contact: ContactCreate):
    with SessionLocal() as db:
        contact = db.query(ContactDB).get(contact_id)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")

        for field, value in updated_contact.dict(exclude_unset=True).items():
            setattr(contact, field, value)

        db.commit()
        db.refresh(contact)
    return ContactResponse(**contact.__dict__)

@app.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_contact(contact_id: int):
    with SessionLocal() as db:
        contact = db.query(ContactDB).get(contact_id)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")

        db.delete(contact)
        db.commit()
    return ContactResponse(**contact.__dict__)

@app.get("/upcoming_birthdays/", response_model=list[ContactResponse])
def upcoming_birthdays():
    with SessionLocal() as db:
        end_date = date.today() + timedelta(days=7)
        contacts = db.query(ContactDB).filter(
            (ContactDB.birthday >= date.today()) & (ContactDB.birthday <= end_date)
        ).all()
    return [ContactResponse(**contact.__dict__) for contact in contacts]
