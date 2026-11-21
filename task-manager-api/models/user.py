import hashlib

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.clock import utc_now

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):

        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        try:
            if self.password and check_password_hash(self.password, pwd):
                return True
        except (TypeError, ValueError):
            pass
        legacy = hashlib.md5(pwd.encode()).hexdigest()
        if self.password == legacy or self.password == pwd:
            self.set_password(pwd)
            db.session.commit()
            return True
        return False

    def is_admin(self):
        if self.role == 'admin':
            return True
        else:
            return False
