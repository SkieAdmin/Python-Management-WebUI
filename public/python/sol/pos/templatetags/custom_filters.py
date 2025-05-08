from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return value * arg
@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary safely."""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def add(value, arg):
    """Concatenate value and arg."""
    return str(value) + str(arg)

@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None