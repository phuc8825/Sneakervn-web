from app import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    order_code = db.Column(db.String(30), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Customer info (for receipt)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    customer_email = db.Column(db.String(150))

    total_amount = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Integer, default=0)
    final_amount = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(50), default='cash')  # cash, card, transfer
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default='completed')  # PoS = usually immediate
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    STATUS_LABELS = {
        'completed': ('Hoàn thành', 'green'),
        'refunded': ('Hoàn trả', 'red'),
        'voided': ('Đã hủy', 'gray'),
    }

    PAYMENT_LABELS = {
        'cash': 'Tiền mặt',
        'card': 'Thẻ ngân hàng',
        'transfer': 'Chuyển khoản',
    }

    def get_status_label(self):
        return self.STATUS_LABELS.get(self.status, (self.status, 'gray'))

    def get_payment_label(self):
        return self.PAYMENT_LABELS.get(self.payment_method, self.payment_method)


class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    product_image = db.Column(db.String(500))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product')