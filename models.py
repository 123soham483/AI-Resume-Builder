from app import db
from datetime import datetime
from flask_login import UserMixin
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    resumes = db.relationship('Resume', backref='user', lazy=True)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    template_id = db.Column(db.String(50), nullable=False, default='modern')
    
    # JSON fields stored as text
    personal_info = db.Column(db.Text, nullable=False)
    education = db.Column(db.Text, nullable=False)
    experience = db.Column(db.Text, nullable=False)
    skills = db.Column(db.Text, nullable=False)
    
    def __init__(self, uuid, title, template_id='modern', personal_info=None, education=None, 
                 experience=None, skills=None, user_id=None):
        self.uuid = uuid
        self.title = title
        self.template_id = template_id
        self.user_id = user_id
        
        # Convert dictionaries/lists to JSON strings
        self.personal_info = json.dumps(personal_info or {})
        self.education = json.dumps(education or [])
        self.experience = json.dumps(experience or [])
        self.skills = json.dumps(skills or [])
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'title': self.title,
            'template_id': self.template_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'personal_info': json.loads(self.personal_info),
            'education': json.loads(self.education),
            'experience': json.loads(self.experience),
            'skills': json.loads(self.skills)
        }

class JobDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text, nullable=True)  # JSON array of keywords
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, title, description, company=None, keywords=None, user_id=None):
        self.title = title
        self.description = description
        self.company = company
        self.user_id = user_id
        self.keywords = json.dumps(keywords or [])
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'description': self.description,
            'keywords': json.loads(self.keywords),
            'created_at': self.created_at.isoformat()
        }
