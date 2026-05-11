from flask import Blueprint, request, jsonify, session, render_template
from flask_login import login_required
from app.models.product import Product

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/')
@login_required
def cart_page():
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)


@cart_bp.route('/api/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')

    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        return jsonify({'success': False, 'message': 'Không tìm thấy sản phẩm'}), 404

    if product.stock <= 0:
        return jsonify({'success': False, 'message': 'Sản phẩm đã hết hàng'}), 400

    if 'cart' not in session:
        session['cart'] = []

    # Tăng số lượng nếu đã có trong giỏ
    for item in session['cart']:
        if item['product_id'] == product_id:
            if item['quantity'] >= product.stock:
                return jsonify({'success': False, 'message': 'Không đủ hàng trong kho'}), 400
            item['quantity'] += 1
            session.modified = True
            return jsonify({'success': True, 'message': 'Đã cập nhật giỏ hàng'})

    # Thêm mới
    session['cart'].append({
        'product_id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': 1
    })
    session.modified = True
    return jsonify({'success': True, 'message': 'Đã thêm vào giỏ hàng'})


@cart_bp.route('/api/update', methods=['POST'])
@login_required
def update_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    if quantity <= 0:
        return jsonify({'success': False, 'message': 'Số lượng không hợp lệ'}), 400

    product = Product.query.get(product_id)
    if product and quantity > product.stock:
        return jsonify({'success': False, 'message': f'Chỉ còn {product.stock} sản phẩm trong kho'}), 400

    if 'cart' in session:
        for item in session['cart']:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                session.modified = True
                break

    return jsonify({'success': True})


@cart_bp.route('/api/remove', methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json()
    product_id = data.get('product_id')

    if 'cart' in session:
        session['cart'] = [i for i in session['cart'] if i['product_id'] != product_id]
        session.modified = True

    return jsonify({'success': True})


@cart_bp.route('/api/count')
def cart_count():
    cart = session.get('cart', [])
    count = sum(item.get('quantity', 1) for item in cart)
    return jsonify({'count': count})