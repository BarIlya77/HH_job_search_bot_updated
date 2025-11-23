from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, UTC

Base = declarative_base()

class Vacancy(Base):
    __tablename__ = 'vacancies'

    id = Column(Integer, primary_key=True)
    hh_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(500))
    company = Column(String(255))
    salary_from = Column(Float)
    salary_to = Column(Float)
    salary_currency = Column(String(10))
    experience = Column(String(100))
    employment = Column(String(100))
    description = Column(Text)
    skills = Column(Text)
    url = Column(String(500))

    # Статусы обработки
    processed = Column(Boolean, default=False)
    cover_letter_generated = Column(Boolean, default=False)
    cover_letter = Column(Text)
    cover_letter_generated_at = Column(DateTime)

    # Отправка отклика
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.now(UTC))

    def __repr__(self):
        return f"<Vacancy(id={self.id}, name='{self.name}', company='{self.company}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'hh_id': self.hh_id,
            'name': self.name,
            'company': self.company,
            'salary_from': self.salary_from,
            'salary_to': self.salary_to,
            'url': self.url,
            'processed': self.processed,
            'cover_letter_generated': self.cover_letter_generated,
            'applied': self.applied,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
