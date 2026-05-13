from flask import Blueprint, redirect, flash, session, render_template, request, url_for
from flask_login import login_required, current_user
from app import db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.email_service import send_order_email
import random
import string

order_bp = Blueprint('order', __name__)


def generate_order_code():
    """Tạo mã đơn hàng duy nhất, ví dụ: SNK-A3X9K2"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    code = f"SNK-{suffix}"
    # Đảm bảo không trùng
    while Order.query.filter_by(order_code=code).first():
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"SNK-{suffix}"
    return code


@order_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Giỏ hàng trống!', 'danger')
        return redirect('/cart')

    cart = session['cart']

    # Lấy thông tin form
    customer_name = request.form.get('customer_name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    notes = request.form.get('notes', '').strip()

    if not all([customer_name, phone, email, address]):
        flash('Vui lòng điền đầy đủ thông tin giao hàng!', 'danger')
        return redirect('/cart')

    # Kiểm tra stock từng sản phẩm
    product_map = {}
    for item in cart:
        product = Product.query.get(item['product_id'])
        if not product or not product.is_active:
            flash(f'Sản phẩm "{item["name"]}" không còn tồn tại!', 'danger')
            return redirect('/cart')
        if product.stock < item['quantity']:
            flash(f'"{product.name}" chỉ còn {product.stock} sản phẩm trong kho!', 'danger')
            return redirect('/cart')
        product_map[product.id] = product

    total_amount = sum(item['price'] * item['quantity'] for item in cart)
    order_code = generate_order_code()

    try:
        # Tạo đơn hàng — dùng đúng tên field trong model Order
        order = Order(
            order_code=order_code,
            user_id=current_user.id,
            customer_name=customer_name,
            customer_phone=phone,
            customer_email=email,
            shipping_address=address,
            total_amount=total_amount,
            notes=notes,
            status='pending',
            payment_method='COD',
        )
        db.session.add(order)
        db.session.flush()  # Lấy order.id trước khi commit

        # Tạo order items & trừ tồn kho
        for item in cart:
            product = product_map[item['product_id']]
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_image=product.image,
                quantity=item['quantity'],
                price=item['price'],
                subtotal=item['price'] * item['quantity'],
            )
            product.stock -= item['quantity']
            db.session.add(order_item)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print("Lỗi tạo đơn hàng:", e)
        flash('Có lỗi xảy ra khi đặt hàng. Vui lòng thử lại!', 'danger')
        return redirect('/cart')

    # Gửi email xác nhận (không chặn nếu lỗi)
    try:
        send_order_email(email, order_code, cart, total_amount, customer_name, phone, address)
    except Exception as e:
        print("Lỗi gửi email:", e)

    # Xóa giỏ hàng
    session.pop('cart', None)

    flash(f' Đặt hàng thành công! Mã đơn hàng: {order_code}', 'success')
    return redirect(url_for('order.order_success', code=order_code))


@order_bp.route('/success')
@login_required
def order_success():
    order_code = request.args.get('code', '')
    order = Order.query.filter_by(order_code=order_code, user_id=current_user.id).first()
    return render_template('order_success.html', order=order)


@order_bp.route('/my-orders')
@login_required
def my_orders():
    orders = (
        Order.query
        .filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template('my_orders.html', orders=orders)