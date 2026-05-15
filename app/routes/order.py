from flask import Blueprint, redirect, flash, session, render_template, request, url_for
from flask_login import login_required, current_user
from app import db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.email_service import send_order_email
from app.utils.decorators import tenant_required
import random
import string

order_bp = Blueprint('order', __name__)


def generate_order_code():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    code = f"ORD-{suffix}"
    while Order.query.filter_by(order_code=code).first():
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"ORD-{suffix}"
    return code


@order_bp.route('/checkout', methods=['POST'])
@login_required
@tenant_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Giỏ hàng trống!', 'danger')
        return redirect('/cart')

    cart = session['cart']

    customer_name = request.form.get('customer_name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()

    if not all([customer_name, phone, email]):
        flash('Vui lòng điền đầy đủ thông tin khách hàng!', 'danger')
        return redirect('/cart')

    product_map = {}
    for item in cart:
        product = Product.query.filter_by(id=item['product_id'], tenant_id=current_user.tenant_id).first()
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
        order = Order(
            order_code=order_code,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            customer_name=customer_name,
            customer_phone=phone,
            customer_email=email,
            total_amount=total_amount,
            status='completed',
            payment_method='COD',
        )
        db.session.add(order)
        db.session.flush()

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

    try:
        send_order_email(email, order_code, cart, total_amount, customer_name, phone, current_user.tenant)
    except Exception as e:
        print("Lỗi gửi email:", e)

    session.pop('cart', None)

    flash(f'Giao dịch thành công! Mã đơn hàng: {order_code}', 'success')
    return redirect(url_for('order.order_success', code=order_code))


@order_bp.route('/success')
@login_required
@tenant_required
def order_success():
    order_code = request.args.get('code', '')
    order = Order.query.filter_by(order_code=order_code, tenant_id=current_user.tenant_id).first()
    return render_template('order_success.html', order=order)


@order_bp.route('/my-orders')
@login_required
@tenant_required
def my_orders():
    orders = (
        Order.query
        .filter_by(tenant_id=current_user.tenant_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template('my_orders.html', orders=orders)