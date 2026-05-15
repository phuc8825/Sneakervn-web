from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.services.email_service import send_receipt_email
import random, string
from datetime import datetime, date

pos_bp = Blueprint('pos', __name__)

def generate_order_code(tenant_id):
    prefix = f"T{tenant_id}-"
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    code = f"{prefix}{suffix}"
    while Order.query.filter_by(order_code=code).first():
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"{prefix}{suffix}"
    return code

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@pos_bp.route('/')
@login_required
def dashboard():
    tid = current_user.tenant_id
    today = date.today()

    total_products = Product.query.filter_by(tenant_id=tid, is_active=True).count()
    total_orders_today = (Order.query
        .filter_by(tenant_id=tid)
        .filter(db.func.date(Order.created_at) == today)
        .count())
    revenue_today = (db.session.query(db.func.sum(Order.final_amount))
        .filter(Order.tenant_id == tid, Order.status == 'completed',
                db.func.date(Order.created_at) == today)
        .scalar() or 0)
    revenue_total = (db.session.query(db.func.sum(Order.final_amount))
        .filter(Order.tenant_id == tid, Order.status == 'completed')
        .scalar() or 0)

    recent_orders = (Order.query
        .filter_by(tenant_id=tid)
        .order_by(Order.created_at.desc())
        .limit(10).all())

    low_stock = (Product.query
        .filter_by(tenant_id=tid, is_active=True)
        .filter(Product.stock <= 5)
        .order_by(Product.stock)
        .limit(5).all())

    return render_template('dashboard.html',
        total_products=total_products,
        total_orders_today=total_orders_today,
        revenue_today=revenue_today,
        revenue_total=revenue_total,
        recent_orders=recent_orders,
        low_stock=low_stock,
    )

# ─── POS TERMINAL ────────────────────────────────────────────────────────────

@pos_bp.route('/pos')
@login_required
def pos_terminal():
    tid = current_user.tenant_id
    category = request.args.get('category', '')
    search = request.args.get('q', '').strip()

    query = Product.query.filter_by(tenant_id=tid, is_active=True)
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    products = query.order_by(Product.name).all()

    categories = (db.session.query(Product.category)
        .filter_by(tenant_id=tid, is_active=True)
        .filter(Product.category != None)
        .distinct().all())
    categories = [c[0] for c in categories]

    return render_template('pos.html',
        products=products,
        categories=categories,
        selected_category=category,
        search=search,
    )

@pos_bp.route('/pos/checkout', methods=['POST'])
@login_required
def checkout():
    data = request.get_json()
    tid = current_user.tenant_id

    items = data.get('items', [])
    customer_name = data.get('customer_name', 'Khách lẻ').strip() or 'Khách lẻ'
    customer_email = data.get('customer_email', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    payment_method = data.get('payment_method', 'cash')
    discount = int(data.get('discount', 0))
    notes = data.get('notes', '').strip()

    if not items:
        return jsonify({'success': False, 'message': 'Chưa có sản phẩm trong giỏ'}), 400

    # Validate products belong to this tenant
    product_map = {}
    for item in items:
        product = Product.query.filter_by(id=item['product_id'], tenant_id=tid, is_active=True).first()
        if not product:
            return jsonify({'success': False, 'message': f'Sản phẩm không tồn tại hoặc không thuộc cửa hàng này'}), 400
        qty = int(item['quantity'])
        if product.stock < qty:
            return jsonify({'success': False, 'message': f'"{product.name}" chỉ còn {product.stock} trong kho'}), 400
        product_map[product.id] = (product, qty)

    total_amount = sum(product_map[pid][0].price * product_map[pid][1] for pid in product_map)
    final_amount = max(0, total_amount - discount)

    order_code = generate_order_code(tid)

    try:
        order = Order(
            tenant_id=tid,
            order_code=order_code,
            user_id=current_user.id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            total_amount=total_amount,
            discount=discount,
            final_amount=final_amount,
            payment_method=payment_method,
            notes=notes,
            status='completed',
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            product, qty = product_map[int(item['product_id'])]
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_image=product.image,
                quantity=qty,
                price=product.price,
                subtotal=product.price * qty,
            )
            product.stock -= qty
            db.session.add(order_item)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Lỗi tạo đơn:", e)
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra, vui lòng thử lại'}), 500

    # Gửi email receipt nếu có email
    if customer_email:
        try:
            send_receipt_email(
                to_email=customer_email,
                order_code=order_code,
                items=[{'name': product_map[int(i['product_id'])][0].name,
                        'quantity': int(i['quantity']),
                        'price': product_map[int(i['product_id'])][0].price}
                       for i in items],
                total_amount=total_amount,
                discount=discount,
                final_amount=final_amount,
                customer_name=customer_name,
                payment_method=payment_method,
                tenant_name=current_user.tenant.name,
                tenant_phone=current_user.tenant.phone or '',
            )
        except Exception as e:
            print("Lỗi gửi email:", e)

    return jsonify({
        'success': True,
        'order_code': order_code,
        'order_id': order.id,
        'message': f'Giao dịch {order_code} hoàn thành!'
    })

# ─── RECEIPT ─────────────────────────────────────────────────────────────────

@pos_bp.route('/receipt/<int:order_id>')
@login_required
def receipt(order_id):
    # Only allow access to orders within the same tenant
    order = Order.query.filter_by(id=order_id, tenant_id=current_user.tenant_id).first_or_404()
    return render_template('receipt.html', order=order)

# ─── ORDERS ──────────────────────────────────────────────────────────────────

@pos_bp.route('/orders')
@login_required
def orders():
    tid = current_user.tenant_id
    search = request.args.get('q', '').strip()
    status = request.args.get('status', '')

    query = Order.query.filter_by(tenant_id=tid)
    if search:
        query = query.filter(
            Order.order_code.ilike(f'%{search}%') |
            Order.customer_name.ilike(f'%{search}%') |
            Order.customer_phone.ilike(f'%{search}%')
        )
    if status:
        query = query.filter_by(status=status)

    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders, search=search, selected_status=status)

# ─── PRODUCTS ────────────────────────────────────────────────────────────────

@pos_bp.route('/products')
@login_required
def products():
    tid = current_user.tenant_id
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '')

    query = Product.query.filter_by(tenant_id=tid)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.created_at.desc()).all()

    categories = (db.session.query(Product.category)
        .filter_by(tenant_id=tid)
        .filter(Product.category != None)
        .distinct().all())
    categories = [c[0] for c in categories]

    return render_template('products.html',
        products=products, categories=categories,
        search=search, selected_category=category)