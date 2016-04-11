from django import template
from django.template.loader import render_to_string
from ..wrapper.wrapper import ViciWrapper, ViciSocketException

register = template.Library()


@register.assignment_tag(takes_context=True, name="vici_reachable")
def vici_reachable(context):
    try:
        ViciWrapper()
        return True
    except ViciSocketException as e:
        return False


@register.simple_tag(name="vici_checker")
def vici_checker():
    return render_to_string('vici/checker.html')