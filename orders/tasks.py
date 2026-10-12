import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import Order

logger = logging.getLogger(__name__)


@shared_task(name="orders.send_order_confirmation_email")
def send_order_confirmation_email(order_id):
    try:
        order = (
            Order.objects.select_related("student")
            .prefetch_related("items__course")
            .get(pk=order_id)
        )
    except Order.DoesNotExist:
        logger.warning("Cannot send confirmation: order %s does not exist", order_id)
        return False

    recipient = order.student.email
    if not recipient:
        logger.info("Order %s has no customer email; skipping confirmation", order_id)
        return False

    context = {"order": order, "items": order.items.all()}
    html_body = render_to_string("orders/order_confirmation.html", context)
    email = EmailMultiAlternatives(
        subject=f"Order confirmation #{order.pk}",
        body=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    email.attach_alternative(html_body, "text/html")
    return email.send()
