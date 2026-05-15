from app import db
from datetime import datetime


class Tenant(db.Model):
    __tablename__ = 'tenant'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    logo = db.Column(db.String(500))
    website = db.Column(db.String(255))
    tax_id = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='tenant', lazy=True, cascade='all, delete-orphan')
    products = db.relationship('Product', backref='tenant', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='tenant', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Tenant {self.name}>'
