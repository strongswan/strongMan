from django import template

register = template.Library()


@register.filter(name='field_type')
def field_type(field):
    return field.field.widget.__class__.__name__


@register.filter(name='get_choice')
def get_choice(text):
    return text[-1:]


@register.filter(name='classname')
def classname(value):
    return value.__class__.__name__
