"""
Chạy script này một lần để tạo bảng trong Supabase và tạo tài khoản admin.
    python create_db.py
"""
from app import create_app, db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Đã tạo tất cả bảng trong database!")

    # Tạo admin mặc định nếu chưa có
    if not User.query.filter_by(email='admin@sneakersvn.com').first():
        admin = User(
            name='Admin',
            email='admin@sneakersvn.com',
            password=generate_password_hash('admin123'),
            role='admin',
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Đã tạo tài khoản admin:")
        print("   Email: admin@sneakersvn.com")
        print("   Mật khẩu: admin123")
        print("   ⚠️  Hãy đổi mật khẩu sau khi đăng nhập!")
    else:
        print("ℹ️  Tài khoản admin đã tồn tại.")

    print("\nDone! Chạy 'python run.py' để khởi động server.")