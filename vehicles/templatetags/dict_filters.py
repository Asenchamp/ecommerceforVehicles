from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None or not isinstance(dictionary, dict):
        return []  # Return an empty list if dictionary is None or not a dict
    return dictionary.get(key, [])

@register.filter
def instance_of(obj, class_name):
    """Check if the object is an instance of a given class name."""
    return obj.__class__.__name__ == class_name