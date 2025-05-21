# custom_filters.py: Custom Django template filters for dynamic table rendering.
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Safely get a value from a dictionary by key for use in Django templates.
    Returns an empty string if the key is not present.
    """
    return dictionary.get(key, "")
