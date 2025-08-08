import sqlalchemy
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name_surname = Column(String(201), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    medical_field = Column(String(100))
    organization = Column(String(255))
    diploma_number = Column(String(100))
    years_experience = Column(Integer, default=0)
    phone = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    doctor_title = Column(String(50), default='Dr.')
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

