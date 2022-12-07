from django import forms
from django.forms import ModelForm

# FORM presets
from api.models import ApiKey, Image


class PermissionMultipleChoiceFormField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


# FORMS
class PermissionForm(forms.Form):
    name = forms.CharField(max_length=200, label="Permission name",
                           widget=forms.TextInput(attrs={'autocomplete': 'off'}))


class ApiKeyForm(ModelForm):
    class Meta:
        model = ApiKey
        fields = ['permission']

    def __init__(self, *args, **kwargs):
        permission = kwargs.pop('permission', '')
        selected_permission = kwargs.pop('current_permission', '')
        edit = kwargs.pop('edit', '')
        name = kwargs.pop('name', '')
        super(ApiKeyForm, self).__init__(*args, **kwargs)

        self.fields["permission"] = PermissionMultipleChoiceFormField(queryset=permission, initial=selected_permission,
                                                                      widget=forms.CheckboxSelectMultiple(),
                                                                      label="Permission", required=False)
        self.fields["length"] = forms.IntegerField(initial=40, label="Length", label_suffix=": ", disabled=edit,
                                                   max_value=200, min_value=10)
        self.fields["name"] = forms.CharField(max_length=200, initial=name,
                                              widget=forms.TextInput(
                                                  attrs={'autocomplete': 'off'}))


class UrlShortenerForm(forms.Form):
    # url = forms.CharField(max_length=20000, label="URL",
    #                       widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    # short_id = forms.CharField(max_length=200, label="Short ID",
    #                            widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def __init__(self, *args, **kwargs):
        short_id = kwargs.pop('short_id', '')
        url = kwargs.pop('url', '')
        edit = kwargs.pop('edit', '')
        super(UrlShortenerForm, self).__init__(*args, **kwargs)
        self.fields["short_id"] = forms.CharField(max_length=200, initial=short_id, required=False, disabled=edit,
                                                  widget=forms.TextInput(
                                                      attrs={'autocomplete': 'off'}))
        self.fields["url"] = forms.CharField(max_length=20000, initial=url,
                                             widget=forms.TextInput(
                                                 attrs={'autocomplete': 'off'}))


class StoreItemForm(forms.Form):

    def __init__(self, name, value, confidential, *args, **kwargs):
        super(StoreItemForm, self).__init__(*args, **kwargs)
        self.fields["name"] = forms.CharField(max_length=200, initial=name,
                                              widget=forms.TextInput(attrs={'autocomplete': 'off'}))
        self.fields["value"] = forms.CharField(max_length=50000, initial=value,
                                               widget=forms.TextInput(attrs={'autocomplete': 'off'}))
        self.fields["confidential"] = forms.BooleanField(initial=confidential, required=False)


class UploadOrEditImageForm(ModelForm):
    class Meta:
        model = Image
        fields = ('title', 'image', 'tags')
