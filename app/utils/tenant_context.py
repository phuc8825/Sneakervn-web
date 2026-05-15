from flask import session, g, redirect, flash
from functools import wraps
from flask_login import current_user
from app.models.tenant import Tenant


def get_tenant_id():
    if current_user.is_authenticated:
        return current_user.tenant_id
    return session.get('tenant_id')


def get_current_tenant():
    tenant_id = get_tenant_id()
    if tenant_id:
        return Tenant.query.get(tenant_id)
    return None


def require_tenant(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_tenant_id():
            flash('Vui lòng chọn cửa hàng!', 'danger')
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated_function
