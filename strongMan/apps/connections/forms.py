from django.forms import inlineformset_factory
from .models import Connection, Address


ConnectionAddressFormSet = inlineformset_factory(
    Connection,
    Address,
    fields=('value',)
)
