from django import template
from django.template.loader import render_to_string
from ..wrapper.wrapper import ViciWrapper, ViciSocketException

register = template.Library()


@register.simple_tag(name="vici_reachable")
def vici_reachable():
    try:
        ViciWrapper()

        return {'reachable': True}
    except ViciSocketException as e:
        return {'reachable': False, 'message': str(e)}


@register.simple_tag(name="vici_version_supported")
def vici_version_supported():
    '''
    Check if strongSwan has the version 5.4.0 at least
    :return: True or False
    '''
    vici_wrapper = ViciWrapper()
    version_info = vici_wrapper.get_version()
    version_b = version_info['version']
    version = version_b.decode('utf-8')
    splitted = str.split(version, '.')
    major = int(splitted[0])
    minor = int(splitted[1])

    if major > 5:
        return True

    if major == 5 and minor >= 4:
        return True

    return False


@register.simple_tag(name="vici_checker")
def vici_checker():
    return render_to_string('vici/checker.html')
