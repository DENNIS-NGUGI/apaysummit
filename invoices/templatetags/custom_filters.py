from django import template

register = template.Library()

@register.filter
def currency(value):
    """Format number as currency with commas"""
    try:
        value = float(value)
        return "{:,.2f}".format(value)
    except (ValueError, TypeError):
        return value

@register.filter
def ksh(value):
    """Format number as KSH currency with commas"""
    try:
        value = float(value)
        return "KES {:,.2f}".format(value)
    except (ValueError, TypeError):
        return value

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_field(form, field_name):
    return form[field_name]