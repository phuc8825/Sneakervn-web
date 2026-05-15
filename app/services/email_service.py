from flask_mail import Message
from flask import current_app
from app import mail
from datetime import datetime

def send_receipt_email(to_email, order_code, items, total_amount, discount,
                       final_amount, customer_name, payment_method, tenant_name, tenant_phone=''):
    """Gửi email biên lai (receipt) cho khách hàng sau giao dịch PoS."""
    if not to_email:
        return

    payment_labels = {
        'cash': 'Tiền mặt',
        'card': 'Thẻ ngân hàng',
        'transfer': 'Chuyển khoản',
    }
    payment_display = payment_labels.get(payment_method, payment_method)

    items_html = ''.join(
        f"""
        <tr>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;">{item['name']}</td>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:center;">{item['quantity']}</td>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{item['price']:,.0f} ₫</td>
            <td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:right;">{item['price'] * item['quantity']:,.0f} ₫</td>
        </tr>
        """
        for item in items
    )

    discount_row = ''
    if discount > 0:
        discount_row = f"""
        <div style="text-align:right;margin-top:8px;color:#e53e3e;">
            Giảm giá: -{discount:,.0f} ₫
        </div>
        """

    now = datetime.now().strftime('%d/%m/%Y %H:%M')

    msg = Message(
        subject=f'Biên lai #{order_code} - {tenant_name}',
        sender=current_app.config.get('MAIL_USERNAME'),
        recipients=[to_email]
    )

    msg.html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;">
        <div style="background:#000;padding:24px;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:22px;">{tenant_name}</h1>
            {f'<p style="color:#aaa;margin:6px 0 0;font-size:13px;">{tenant_phone}</p>' if tenant_phone else ''}
        </div>

        <div style="padding:32px;">
            <h2 style="color:#1a1a1a;margin-top:0;">🧾 Biên lai thanh toán</h2>

            <div style="background:#f9f9f9;border-radius:10px;padding:16px 20px;margin-bottom:24px;font-size:14px;">
                <p style="margin:0 0 6px;"><strong>Mã giao dịch:</strong> {order_code}</p>
                <p style="margin:0 0 6px;"><strong>Ngày giờ:</strong> {now}</p>
                <p style="margin:0 0 6px;"><strong>Khách hàng:</strong> {customer_name}</p>
                <p style="margin:0;"><strong>Thanh toán:</strong> {payment_display}</p>
            </div>

            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead>
                    <tr style="background:#f0f0f0;">
                        <th style="padding:10px;text-align:left;">Sản phẩm</th>
                        <th style="padding:10px;text-align:center;">SL</th>
                        <th style="padding:10px;text-align:right;">Đơn giá</th>
                        <th style="padding:10px;text-align:right;">Thành tiền</th>
                    </tr>
                </thead>
                <tbody>{items_html}</tbody>
            </table>

            <div style="margin-top:12px;text-align:right;font-size:14px;">
                <div>Tạm tính: {total_amount:,.0f} ₫</div>
                {discount_row}
                <div style="margin-top:10px;padding-top:10px;border-top:2px solid #000;">
                    <strong style="font-size:18px;">TỔNG CỘNG: {final_amount:,.0f} ₫</strong>
                </div>
            </div>

            <p style="color:#888;font-size:12px;margin-top:32px;text-align:center;">
                Cảm ơn bạn đã mua hàng tại {tenant_name}!<br>
                Đây là email tự động, vui lòng không reply.
            </p>
        </div>
    </div>
    """

    mail.send(msg)