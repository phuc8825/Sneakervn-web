from app import db
from datetime import datetime

class Tenant(db.Model):
    __tablename__ = 'tenant'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='tenant', lazy=True)
    products = db.relationship('Product', backref='tenant', lazy=True)
    orders = db.relationship('Order', backref='tenant', lazy=True)

    def __repr__(self):
        return f'<Tenant {self.name}>'