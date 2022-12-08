from django import forms


class AccountForm(forms.Form):
    username = forms.CharField(label="用户名", max_length=128, widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={"class": "form-control"}))


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()
