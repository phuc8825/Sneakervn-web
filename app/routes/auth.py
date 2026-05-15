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
        return redirect(url_for('pos.dashboard'))

    tenants = Tenant.query.filter_by(is_active=True).order_by(Tenant.name).all()

    if request.method == 'POST':
        tenant_id = request.form.get('tenant_id', type=int)
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not tenant_id:
            flash('Vui lòng chọn cửa hàng / tenant!', 'danger')
            return render_template('login.html', tenants=tenants)

        user = User.query.filter_by(email=email, tenant_id=tenant_id).first()

        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash('Tài khoản của bạn đã bị khóa!', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user)
            flash(f'Đăng nhập thành công! Chào {user.name} - {user.tenant.name}', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('pos.dashboard'))
        flash('Email, mật khẩu hoặc cửa hàng không đúng!', 'danger')

    return render_template('login.html', tenants=tenants)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công.', 'info')
    return redirect(url_for('auth.login'))