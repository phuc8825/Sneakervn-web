from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models.product import Product
from app.utils.decorators import tenant_required

product_bp = Blueprint('product', __name__)


@product_bp.route('/')
@login_required
@tenant_required
def home():
    products = (
        Product.query
        .filter_by(is_active=True, tenant_id=current_user.tenant_id)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    return render_template('index.html', products=products)


@product_bp.route('/products')
@login_required
@tenant_required
def products():
    category = request.args.get('category')
    search = request.args.get('q', '').strip()

    query = Product.query.filter_by(is_active=True, tenant_id=current_user.tenant_id)

    if category:
        query = query.filter_by(category=category)

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.order_by(Product.created_at.desc()).all()

    return render_template('products.html', products=products, category=category, search=search)