from django import template
from django.utils import timezone

from core.services import english_date

register = template.Library()


@register.filter
def englishdate(value):
    return english_date(value)


@register.filter
def englishdatetime(value):
    if value is None:
        return ""
    if hasattr(value, "tzinfo"):
        value = timezone.localtime(value)
    return f"{value.strftime('%A, %B')} {value.day}, {value.year} {value.strftime('%H:%M')}"
