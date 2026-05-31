import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from store.choices import OrderStatus

logger = logging.getLogger(__name__)

FOOTER_TAGLINE = "Haznex — Bridging UK Markets to Kenya | vhbridge"

# status -> (subject template, html template, plain intro for generic template)
_STATUS_EMAIL_CONFIG = {
    OrderStatus.PAYMENT_CONFIRMED: (
        "Your Haznex order {order_number} is confirmed — we are sourcing your item",
        "orders/emails/payment_confirmed.html",
        None,
    ),
    OrderStatus.SOURCING_ITEM: (
        "Update on {order_number} — your item is being sourced in the UK",
        "orders/emails/status_update.html",
        "Our UK partner is now locating your item. We will update you as soon as it is secured.",
    ),
    OrderStatus.SHIPPED_FROM_UK: (
        "{order_number} has been shipped from the UK",
        "orders/emails/shipped_from_uk.html",
        None,
    ),
    OrderStatus.IN_TRANSIT: (
        "{order_number} is in transit to Kenya",
        "orders/emails/status_update.html",
        "Your item is in transit to Kenya. Estimated delivery is based on your chosen shipping method.",
    ),
    OrderStatus.ARRIVED_IN_KENYA: (
        "Great news — {order_number} has arrived in Kenya",
        "orders/emails/arrived_in_kenya.html",
        None,
    ),
    OrderStatus.OUT_FOR_DELIVERY: (
        "{order_number} is out for delivery today",
        "orders/emails/status_update.html",
        "Your item is on its way to your delivery address today.",
    ),
    OrderStatus.COMPLETED: (
        "Your Haznex order {order_number} has been delivered — thank you",
        "orders/emails/completed.html",
        None,
    ),
    OrderStatus.CANCELLED: (
        "Your Haznex order {order_number} has been cancelled",
        "orders/emails/status_update.html",
        "This order has been cancelled. If you have questions, please contact us.",
    ),
}


def _build_tracking_url(order_number):
    base = settings.SITE_URL.rstrip("/")
    return f"{base}/orders/{order_number}/"


def _build_email_context(order, status_update):
    status = status_update.status
    status_labels = dict(OrderStatus.choices)
    shipping = order.shipping_method
    config = _STATUS_EMAIL_CONFIG.get(status)
    intro = config[2] if config else ""
    return {
        "order_number": order.order_number,
        "product_name": order.product.name,
        "status_display": status_labels.get(status, status),
        "admin_note": status_update.note.strip() if status_update.note else "",
        "tracking_url": _build_tracking_url(order.order_number),
        "footer_tagline": FOOTER_TAGLINE,
        "shipping_method_name": shipping.name,
        "estimated_delivery_days": shipping.estimated_delivery_days,
        "show_estimated_delivery": status == OrderStatus.IN_TRANSIT,
        "email_intro": intro,
    }


def _plain_text_body(context):
    lines = [
        f"Order: {context['order_number']}",
        f"Product: {context['product_name']}",
        f"Status: {context['status_display']}",
    ]
    if context.get("email_intro"):
        lines.append("")
        lines.append(context["email_intro"])
    if context.get("admin_note"):
        lines.append("")
        lines.append(f"Note: {context['admin_note']}")
    lines.extend(
        [
            "",
            f"Track your order: {context['tracking_url']}",
            "",
            context["footer_tagline"],
        ]
    )
    return "\n".join(lines)


def send_order_status_email(order, status_update):
    """
    Send an HTML status email to the client when notifications are enabled.
    Silently returns when disabled, status is not emailable, or client has no email.
    """
    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        logger.debug(
            "Email notifications disabled; skipping status email for %s (%s)",
            order.order_number,
            status_update.status,
        )
        return

    status = status_update.status
    config = _STATUS_EMAIL_CONFIG.get(status)
    if not config:
        logger.debug(
            "No email template for status %s on order %s; skipping",
            status,
            order.order_number,
        )
        return

    recipient = (order.client.email or "").strip()
    if not recipient:
        logger.debug(
            "No client email for order %s; skipping status email",
            order.order_number,
        )
        return

    subject_template, template_name, _ = config
    subject = subject_template.format(order_number=order.order_number)

    from orders.models import Order

    order = Order.objects.select_related(
        "product", "shipping_method", "client"
    ).get(pk=order.pk)

    context = _build_email_context(order, status_update)
    html_body = render_to_string(template_name, context)
    text_body = _plain_text_body(context)

    from_email = settings.DEFAULT_FROM_EMAIL
    # Gmail SMTP requires the authenticated account as the sender.
    if settings.EMAIL_HOST_USER and "gmail" in (settings.EMAIL_HOST or "").lower():
        from_email = f"Haznex <{settings.EMAIL_HOST_USER}>"

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[recipient],
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
        logger.info(
            "Status email sent for order %s (%s) to %s",
            order.order_number,
            status,
            recipient,
        )
    except Exception:
        logger.exception(
            "Failed to send status email for order %s (%s)",
            order.order_number,
            status,
        )
