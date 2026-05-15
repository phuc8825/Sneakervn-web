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

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin():
            flash('Chỉ Super Admin mới có quyền truy cập!', 'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function