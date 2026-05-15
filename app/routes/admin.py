import os
from flask import Blueprint, render_template, request, redirect, flash, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.utils.decorators import admin_required
from app.models.product import Product
from app.models.order import Order
from app.models.user import User
from app import db

admin_bp = Blueprint('admin', __name__)

CATEGORIES = ['Nam', 'Nữ', 'Unisex', 'Trẻ em']
ORDER_STATUSES = ['pending', 'completed', 'cancelled']


def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    )


def save_image(image_file):
    if not image_file or not allowed_file(image_file.filename):
        return None
    filename = secure_filename(image_file.filename)
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    image_file.save(upload_path)
    return filename


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_products = Product.query.filter_by(tenant_id=current_user.tenant_id).count()
    total_orders = Order.query.filter_by(tenant_id=current_user.tenant_id).count()
    total_users = User.query.filter_by(tenant_id=current_user.tenant_id).count()
    pending_orders = Order.query.filter_by(tenant_id=current_user.tenant_id, status='pending').count()
    recent_orders = Order.query.filter_by(tenant_id=current_user.tenant_id).order_by(Order.created_at.desc()).limit(10).all()

    total_revenue = db.session.query(
        db.func.sum(Order.total_amount)
    ).filter(Order.tenant_id == current_user.tenant_id, Order.status == 'completed').scalar() or 0

    return render_template(
        'admin/dashboard.html',
        total_products=total_products,
        total_orders=total_orders,
        total_users=total_users,
        pending_orders=pending_orders,
        recent_orders=recent_orders,
        total_revenue=total_revenue,
    )


@admin_bp.route('/products')
@login_required
@admin_required
def products():
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '')

    query = Product.query.filter_by(tenant_id=current_user.tenant_id)
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

    product = Product(
        tenant_id=current_user.tenant_id,
        name=name,
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
    product = Product.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()

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
    product = Product.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Đã xóa sản phẩm "{name}".', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_product(id):
    product = Product.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    product.is_active = not product.is_active
    db.session.commit()
    status = 'hiển thị' if product.is_active else 'ẩn'
    flash(f'Đã {status} sản phẩm "{product.name}".', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    status = request.args.get('status', '')
    search = request.args.get('q', '').strip()

    query = Order.query.filter_by(tenant_id=current_user.tenant_id)
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
    order = Order.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    return render_template('admin/order_detail.html', order=order, statuses=ORDER_STATUSES)


@admin_bp.route('/orders/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    order = Order.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    new_status = request.form.get('status')

    if new_status not in ORDER_STATUSES:
        flash('Trạng thái không hợp lệ!', 'danger')
        return redirect(url_for('admin.order_detail', id=id))

    if new_status == 'cancelled' and order.status != 'cancelled':
        for item in order.items:
            if item.product:
                item.product.stock += item.quantity

    order.status = new_status
    db.session.commit()
    flash('Đã cập nhật trạng thái đơn hàng!', 'success')
    return redirect(url_for('admin.order_detail', id=id))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    search = request.args.get('q', '').strip()
    query = User.query.filter_by(tenant_id=current_user.tenant_id)
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
    user = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    user.is_active = not user.is_active
    db.session.commit()
    status = 'kích hoạt' if user.is_active else 'khóa'
    flash(f'Đã {status} tài khoản "{user.name}".', 'success')
    return redirect(url_for('admin.users'))