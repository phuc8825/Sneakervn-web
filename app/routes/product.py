from flask import Blueprint, render_template, request
from app.models.product import Product

product_bp = Blueprint('product', __name__)


@product_bp.route('/')
def home():
    # Lấy sản phẩm nổi bật (8 sản phẩm mới nhất, đang active)
    products = (
        Product.query
        .filter_by(is_active=True)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    return render_template('index.html', products=products)


@product_bp.route('/products')
def products():
    category = request.args.get('category')
    search = request.args.get('q', '').strip()

    query = Product.query.filter_by(is_active=True)

    if category:
        query = query.filter_by(category=category)

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.order_by(Product.created_at.desc()).all()

    return render_template('products.html', products=products, category=category, search=search)