from flask import Blueprint, render_template, redirect, request, flash, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.tenant import Tenant

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('product.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash('Tài khoản của bạn đã bị khóa!', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user)

            next_page = request.args.get('next')
            return redirect(next_page or url_for('product.home'))

        flash('Email hoặc mật khẩu không đúng!', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('product.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()

        tenant_option = request.form.get('tenant_option', 'new')
        tenant_id = request.form.get('tenant_id', '')

        shop_name = request.form.get('shop_name', '').strip()
        shop_email = request.form.get('shop_email', '').strip()
        shop_phone = request.form.get('shop_phone', '').strip()
        shop_address = request.form.get('shop_address', '').strip()

        if not email or not name or not password:
            flash('Vui lòng điền đầy đủ thông tin!', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng!', 'danger')
            return render_template('register.html')

        try:
            if tenant_option == 'new':
                if not shop_name or not shop_email:
                    flash('Vui lòng nhập tên và email cửa hàng!', 'danger')
                    return render_template('register.html')

                tenant = Tenant(
                    name=shop_name,
                    email=shop_email,
                    phone=shop_phone,
                    address=shop_address
                )
                db.session.add(tenant)
                db.session.flush()
            else:
                tenant = Tenant.query.get(int(tenant_id))
                if not tenant:
                    flash('Cửa hàng không tồn tại!', 'danger')
                    return render_template('register.html')

            user = User(
                email=email,
                name=name,
                phone=phone,
                password=generate_password_hash(password),
                tenant_id=tenant.id,
                role='owner' if tenant_option == 'new' else 'staff'
            )
            db.session.add(user)
            db.session.commit()

            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi đăng ký: {str(e)}', 'danger')
            return render_template('register.html')

    tenants = Tenant.query.filter_by(is_active=True).all()
    return render_template('register.html', tenants=tenants)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('product.home'))