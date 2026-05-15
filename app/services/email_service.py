from flask_mail import Message
from flask import current_app
from app import mail


def send_order_email(to_email, order_code, items, total, customer_name, phone, tenant):
    msg = Message(
        subject=f'Xác nhận giao dịch #{order_code} - {tenant.name}',
        sender=current_app.config.get('MAIL_USERNAME'),
        recipients=[to_email]
    )

    items_html = ''.join(
        f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #eee;">{item['name']}</td>
            <td style="padding:10px;border-bottom:1px solid #eee;text-align:center;">{item['quantity']}</td>
            <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;">{item['price']:,.0f} ₫</td>
            <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;">{item['price'] * item['quantity']:,.0f} ₫</td>
        </tr>
        """
        for item in items
    )

    msg.html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#000;padding:24px;text-align:center;">
            <h1 style="color:#fff;margin:0;">{tenant.name}</h1>
        </div>

        <div style="padding:32px;">
            <h2 style="color:#1a1a1a;">🎉 Giao dịch thành công!</h2>
            <p>Xin chào <strong>{customer_name}</strong>,</p>
            <p>Giao dịch của bạn đã được hoàn thành. Cảm ơn bạn đã mua sắm tại {tenant.name}!</p>

            <div style="background:#f5f5f5;border-radius:12px;padding:20px;margin:24px 0;">
                <p style="margin:0 0 8px;"><strong>Mã giao dịch:</strong> {order_code}</p>
                <p style="margin:0 0 8px;"><strong>Số điện thoại:</strong> {phone}</p>
                <p style="margin:0 0 8px;"><strong>Cửa hàng:</strong> {tenant.name}</p>
                <p style="margin:0;"><strong>Địa chỉ:</strong> {tenant.address or ''}</p>
            </div>

            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="background:#f5f5f5;">
                        <th style="padding:10px;text-align:left;">Sản phẩm</th>
                        <th style="padding:10px;text-align:center;">SL</th>
                        <th style="padding:10px;text-align:right;">Đơn giá</th>
                        <th style="padding:10px;text-align:right;">Thành tiền</th>
                    </tr>
                </thead>
                <tbody>{items_html}</tbody>
            </table>

            <div style="text-align:right;margin-top:20px;padding-top:16px;border-top:2px solid #000;">
                <strong style="font-size:20px;">Tổng cộng: {total:,.0f} ₫</strong>
            </div>

            <p style="color:#666;margin-top:32px;">
                Phương thức thanh toán: <strong>COD (Thanh toán khi nhận hàng)</strong>
            </p>
        </div>

        <div style="background:#f5f5f5;padding:20px;text-align:center;color:#666;font-size:13px;">
            © 2024 {tenant.name} — Cảm ơn bạn đã tin tưởng mua sắm!
        </div>
    </div>
    """

    print("Đang gửi mail tới:", to_email)
    mail.send(msg)
    print("Gửi mail thành công")