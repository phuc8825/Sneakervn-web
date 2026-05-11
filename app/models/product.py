from app import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0)

    # Tên file ảnh, ví dụ: "nike-air-max.jpg"
    # File ảnh đặt tại app/static/uploads/<image>
    image = db.Column(db.String(500), default='default.jpg')

    category = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def image_url(self):
        """Trả về đường dẫn ảnh để dùng trong template."""
        return f'uploads/{self.image}'