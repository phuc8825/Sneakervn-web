import os
from flask import Blueprint, render_template, request, redirect, flash, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from app.utils.decorators import admin_required
from app.models.product import Product
from app.models.order import Order
from app.models.user import User
from app import db

admin_bp = Blueprint('admin', __name__)

ORDER_STATUSES = ['completed', 'refunded', 'voided']

def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS'])

def save_image(image_file):
    if not image_file or not allowed_file(image_file.filename):
        return None
    filename = secure_filename(image_file.filename)
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    image_file.save(upload_path)
    return filename

def get_tenant_categories(tenant_id):
    rows = (db.session.query(Product.category)
        .filter_by(tenant_id=tenant_id)
        .filter(Product.category != None)
        .distinct().all())
    defaults = ['Nam', 'Nữ', 'Unisex', 'Trẻ em', 'Phụ kiện']
    existing = [r[0] for r in rows]
    for d in defaults:
        if d not in existing:
            existing.append(d)
    return existing

# ─── PRODUCTS ────────────────────────────────────────────────────────────────

@admin_bp.route('/products')
@login_required
@admin_required
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

    return render_template('admin/products.html',
        products=products,
        categories=get_tenant_categories(tid),
        search=search,
        selected_category=category,
    )

@admin_bp.route('/products/add', methods=['POST'])
@login_required
@admin_required
def add_product():
    tid = current_user.tenant_id
    name = request.form.get('name', '').strip()
    price = request.form.get('price', 0)
    category = request.form.get('category', '').strip()
    brand = request.form.get('brand', '').strip()
    description = request.form.get('description', '').strip()
    stock = request.form.get('stock', 0)

    if not name or not price:
        flash('Tên và giá sản phẩm không được để trống!', 'danger')
        return redirect(url_for('admin.products'))

    image_file = request.files.get('image')
    filename = save_image(image_file) or 'default.jpg'

    product = Product(
        tenant_id=tid,
        name=name,
        price=int(price),
        category=category or None,
        brand=brand or None,
        description=description or None,
        stock=int(stock),
        image=filename,
    )
    db.session.add(product)
    db.session.commit()
    flash(f'✅ Đã thêm sản phẩm "{name}" thành công!', 'success')
    return redirect(url_for('admin.products'))

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    tid = current_user.tenant_id
    product = Product.query.filter_by(id=id, tenant_id=tid).first_or_404()

    if request.method == 'POST':
        product.name = request.form.get('name', product.name).strip()
        product.price = int(request.form.get('price', product.price))
        product.category = request.form.get('category', product.category) or None
        product.brand = request.form.get('brand', product.brand or '').strip() or None
        product.description = request.form.get('description', product.description or '').strip() or None
        product.stock = int(request.form.get('stock', product.stock))
        product.is_active = request.form.get('is_active') == 'on'

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            new_filename = save_image(image_file)
            if new_filename:
                product.image = new_filename

        db.session.commit()
        flash(f'✅ Đã cập nhật sản phẩm "{product.name}" thành công!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/edit_product.html', product=product,
                           categories=get_tenant_categories(tid))

@admin_bp.route('/products/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    tid = current_user.tenant_id
    product = Product.query.filter_by(id=id, tenant_id=tid).first_or_404()
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Đã xóa sản phẩm "{name}".', 'success')
    return redirect(url_for('admin.products'))

@admin_bp.route('/products/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_product(id):
    tid = current_user.tenant_id
    product = Product.query.filter_by(id=id, tenant_id=tid).first_or_404()
    product.is_active = not product.is_active
    db.session.commit()
    status = 'hiển thị' if product.is_active else 'ẩn'
    flash(f'Đã {status} sản phẩm "{product.name}".', 'success')
    return redirect(url_for('admin.products'))

# ─── ORDERS ──────────────────────────────────────────────────────────────────

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    tid = current_user.tenant_id
    status = request.args.get('status', '')
    search = request.args.get('q', '').strip()

    query = Order.query.filter_by(tenant_id=tid)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            Order.order_code.ilike(f'%{search}%') |
            Order.customer_name.ilike(f'%{search}%')
        )

    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html',
        orders=orders, statuses=ORDER_STATUSES, selected_status=status)

@admin_bp.route('/orders/<int:id>')
@login_required
@admin_required
def order_detail(id):
    tid = current_user.tenant_id
    order = Order.query.filter_by(id=id, tenant_id=tid).first_or_404()
    return render_template('admin/order_detail.html', order=order, statuses=ORDER_STATUSES)

@admin_bp.route('/orders/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    tid = current_user.tenant_id
    order = Order.query.filter_by(id=id, tenant_id=tid).first_or_404()
    new_status = request.form.get('status')
    if new_status not in ORDER_STATUSES:
        flash('Trạng thái không hợp lệ!', 'danger')
        return redirect(url_for('admin.order_detail', id=id))

    # Hoàn kho nếu void/refund
    if new_status in ('voided', 'refunded') and order.status == 'completed':
        for item in order.items:
            if item.product:
                item.product.stock += item.quantity

    order.status = new_status
    db.session.commit()
    flash('Đã cập nhật trạng thái giao dịch!', 'success')
    return redirect(url_for('admin.order_detail', id=id))

# ─── USERS ───────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    tid = current_user.tenant_id
    search = request.args.get('q', '').strip()
    query = User.query.filter_by(tenant_id=tid)
    if search:
        query = query.filter(
            User.name.ilike(f'%{search}%') | User.email.ilike(f'%{search}%')
        )
    users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    tid = current_user.tenant_id
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'staff')
    phone = request.form.get('phone', '').strip()

    if not name or not email or not password:
        flash('Vui lòng điền đầy đủ thông tin!', 'danger')
        return redirect(url_for('admin.users'))

    if User.query.filter_by(tenant_id=tid, email=email).first():
        flash('Email đã tồn tại trong cửa hàng này!', 'danger')
        return redirect(url_for('admin.users'))

    user = User(
        tenant_id=tid,
        name=name,
        email=email,
        password=generate_password_hash(password),
        role=role if role in ('admin', 'staff') else 'staff',
        phone=phone or None,
    )
    db.session.add(user)
    db.session.commit()
    flash(f'✅ Đã thêm nhân viên "{name}" thành công!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    tid = current_user.tenant_id
    user = User.query.filter_by(id=id, tenant_id=tid).first_or_404()
    if user.id == current_user.id:
        flash('Không thể tự khóa tài khoản của mình!', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'kích hoạt' if user.is_active else 'khóa'
    flash(f'Đã {status} tài khoản "{user.name}".', 'success')
    return redirect(url_for('admin.users'))