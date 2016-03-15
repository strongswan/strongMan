from django import forms
from .models import UploadFile

class UploadFileForm(forms.Form):
    class Meta:
        model = UploadFile
        fields = "__all__"