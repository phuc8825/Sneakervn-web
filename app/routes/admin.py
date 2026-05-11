import os
from flask import Blueprint, render_template, request, redirect, flash, url_for, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from app.utils.decorators import admin_required
from app.models.product import Product
from app.models.order import Order
from app.models.user import User
from app import db

admin_bp = Blueprint('admin', __name__)

CATEGORIES = ['Nam', 'Nữ', 'Unisex', 'Trẻ em']
ORDER_STATUSES = ['pending', 'confirmed', 'shipping', 'delivered', 'cancelled']


def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    )


def save_image(image_file):
    """Lưu file ảnh vào thư mục uploads, trả về tên file."""
    if not image_file or not allowed_file(image_file.filename):
        return None
    filename = secure_filename(image_file.filename)
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    image_file.save(upload_path)
    return filename


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    total_revenue = db.session.query(
        db.func.sum(Order.total_amount)
    ).filter(Order.status == 'delivered').scalar() or 0

    return render_template(
        'admin/dashboard.html',
        total_products=total_products,
        total_orders=total_orders,
        total_users=total_users,
        pending_orders=pending_orders,
        recent_orders=recent_orders,
        total_revenue=total_revenue,
    )


# ─── PRODUCTS ────────────────────────────────────────────────────────────────

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '')

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)

    products = query.order_by(Product.created_at.desc()).all()
    return render_template(
        'admin/products.html',
        products=products,
        categories=CATEGORIES,
        search=search,
        selected_category=category,
    )


@admin_bp.route('/products/add', methods=['POST'])
@login_required
@admin_required
def add_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', 0)
    category = request.form.get('category', 'Nam')
    brand = request.form.get('brand', '').strip()
    description = request.form.get('description', '').strip()
    stock = request.form.get('stock', 0)

    if not name or not price:
        flash('Tên và giá sản phẩm không được để trống!', 'danger')
        return redirect(url_for('admin.products'))

    image_file = request.files.get('image')
    filename = save_image(image_file) or 'default.jpg'

    # Tạo slug từ tên sản phẩm
    import re, unicodedata
    slug_base = name.lower()
    slug_base = unicodedata.normalize('NFD', slug_base)
    slug_base = ''.join(c for c in slug_base if unicodedata.category(c) != 'Mn')
    slug_base = re.sub(r'[^a-z0-9]+', '-', slug_base).strip('-')
    slug = slug_base
    counter = 1
    while Product.query.filter_by(slug=slug).first():
        slug = f"{slug_base}-{counter}"
        counter += 1

    product = Product(
        name=name,
        slug=slug,
        price=int(price),
        category=category,
        brand=brand,
        description=description,
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
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form.get('name', product.name).strip()
        product.price = int(request.form.get('price', product.price))
        product.category = request.form.get('category', product.category)
        product.brand = request.form.get('brand', product.brand or '').strip()
        product.description = request.form.get('description', product.description or '').strip()
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

    return render_template('admin/edit_product.html', product=product, categories=CATEGORIES)


@admin_bp.route('/products/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Đã xóa sản phẩm "{name}".', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_product(id):
    product = Product.query.get_or_404(id)
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
    status = request.args.get('status', '')
    search = request.args.get('q', '').strip()

    query = Order.query
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            Order.order_code.ilike(f'%{search}%') |
            Order.customer_name.ilike(f'%{search}%') |
            Order.customer_phone.ilike(f'%{search}%')
        )

    orders = query.order_by(Order.created_at.desc()).all()
    return render_template(
        'admin/orders.html',
        orders=orders,
        statuses=ORDER_STATUSES,
        selected_status=status,
    )


@admin_bp.route('/orders/<int:id>')
@login_required
@admin_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order, statuses=ORDER_STATUSES)


@admin_bp.route('/orders/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')

    if new_status not in ORDER_STATUSES:
        flash('Trạng thái không hợp lệ!', 'danger')
        return redirect(url_for('admin.order_detail', id=id))

    # Nếu hủy đơn → hoàn lại stock
    if new_status == 'cancelled' and order.status != 'cancelled':
        for item in order.items:
            if item.product:
                item.product.stock += item.quantity

    order.status = new_status
    db.session.commit()
    flash('Đã cập nhật trạng thái đơn hàng!', 'success')
    return redirect(url_for('admin.order_detail', id=id))


# ─── USERS ───────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    search = request.args.get('q', '').strip()
    query = User.query
    if search:
        query = query.filter(
            User.name.ilike(f'%{search}%') |
            User.email.ilike(f'%{search}%')
        )
    users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'kích hoạt' if user.is_active else 'khóa'
    flash(f'Đã {status} tài khoản "{user.name}".', 'success')
    return redirect(url_for('admin.users'))