from flask import Blueprint, render_template, redirect, request, flash, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User

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

        if not email or not name or not password:
            flash('Vui lòng điền đầy đủ thông tin!', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng!', 'danger')
            return render_template('register.html')

        user = User(
            email=email,
            name=name,
            phone=phone,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('product.home'))