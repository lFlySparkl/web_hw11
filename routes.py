from fastapi import APIRouter, HTTPException, Query
from typing import List
from models import SessionLocal, ContactDB
from schemas import ContactCreate, ContactResponse
from datetime import date, timedelta

router = APIRouter()

@router.post("/contacts/", response_model=ContactResponse)
def create_contact(contact: ContactCreate):
    with SessionLocal() as db:
        db_contact = ContactDB(**contact.dict())
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
    return ContactResponse(**db_contact.__dict__)

@router.get("/contacts/", response_model=List[ContactResponse])
def read_contacts(q: str = Query(None, min_length=3)):
    with SessionLocal() as db:
        if q is None:
            raise HTTPException(status_code=400, detail="Search query cannot be empty or None")
        contacts = db.query(ContactDB).filter(
            (ContactDB.first_name.contains(q)) | 
            (ContactDB.last_name.contains(q)) | 
            (ContactDB.email.contains(q))
        ).all()
    return [ContactResponse(**contact.__dict__) for contact in contacts]

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int):
    with SessionLocal() as db:
        contact = db.query(ContactDB).get(contact_id)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse(**contact.__dict__)

@router.put("/contacts/{contact_id}", response_model=ContactResponse)
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

@router.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_contact(contact_id: int):
    with SessionLocal() as db:
        contact = db.query(ContactDB).get(contact_id)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")

        db.delete(contact)
        db.commit()
    return ContactResponse(**contact.__dict__)

@router.get("/upcoming_birthdays/", response_model=List[ContactResponse])
def upcoming_birthdays():
    with SessionLocal() as db:
        end_date = date.today() + timedelta(days=7)
        contacts = db.query(ContactDB).filter(
            (ContactDB.birthday >= date.today()) & (ContactDB.birthday <= end_date)
        ).all()
    return [ContactResponse(**contact.__dict__) for contact in contacts]
