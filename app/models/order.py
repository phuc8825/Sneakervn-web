from app import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)

    total_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default='pending')
    payment_method = db.Column(db.String(50), default='COD')
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    STATUS_LABELS = {
        'pending': ('Chờ xử lý', 'yellow'),
        'confirmed': ('Đã xác nhận', 'blue'),
        'shipping': ('Đang giao', 'purple'),
        'delivered': ('Đã giao', 'green'),
        'cancelled': ('Đã hủy', 'red'),
    }

    def get_status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'gray'))


class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    product_name = db.Column(db.String(200), nullable=False)
    product_image = db.Column(db.String(500))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product')