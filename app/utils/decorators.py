from functools import wraps
from flask import redirect, flash
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Bạn không có quyền truy cập trang này!', 'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


def tenant_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.tenant_id:
            flash('Vui lòng chọn cửa hàng!', 'danger')
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated_function