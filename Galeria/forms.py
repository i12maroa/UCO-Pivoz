from . import models
from django import forms
from Galeria.models import MyUser, RegularUser, AdminUser, Album, Video
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from django_registration.forms import RegistrationForm






class ImageForm(forms.ModelForm):
    class Meta:
        model = models.Imagen
        fields = ['titulo',
                  'descripcion',
                  'album',
                  'keyword',
                  'fichero_imagen',
                  'image_height',
                  'image_width']

        def __init__(self, *args, **kwargs):
            self.request = kwargs.pop('request', None)
            if (self.request.method == 'POST' and self.request.FILES):
                uploaded_file = self.request.FILES
                self.fields['titulo'] = uploaded_file['fichero_imagen'].name

class ShareUserForm(forms.Form):
    administrador = forms.CharField(label='Administrador con el que quiere compartir el usuario', max_length=100)


# Django-Registration Custom User Model

class AdminUserForm(RegistrationForm):
    class Meta(RegistrationForm.Meta):
        model = AdminUser
        # fields = ['username', 'password', 'telefono', 'email']

    def save(self, commit=True):
        # Save the commit password in hashed form
        user = super().save(commit=False)
        # Set the current User as admin user
        user.is_staff = True
        if commit:
            user.save()
        return user






### --------------  ADMIN FORMS  --------------  ###

### -------------- Generic User ---------------- ###

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required fields,
     plus a repeated password"""
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repita Contraseña',
                                widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ('email',
                  'first_name',
                  'last_name',
                  'telefono',
                  'avatar',
                  'groups',)

        widgets = {
            'telefono' : PhoneNumberPrefixWidget(),
        }

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on the user
    , but replaces the password field with admin's password
    hash display field"""

    password = ReadOnlyPasswordHashField(label=("Contraseña"),
                                         help_text=("Las contraseñas sin procesar no se almacenan, por lo que no hay "
                                                    "forma de ver la contraseña de este usuario, pero puede cambiarla "
                                                    "usando <a href=\'../password/\'>este formulario</a>."))

    class Meta:
        model = RegularUser
        fields = ('username',
                  'email',
                  'password',
                  'first_name',
                  'last_name',
                  'descripcion',
                  'telefono',
                  'avatar',
                  'rfid'
                  )

        widgets = {
            'telefono': PhoneNumberPrefixWidget(),
        }

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]



### -------------- Regular User ---------------- ###

class RegularUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repita contraseña', widget=forms.PasswordInput)

    class Meta:
        model = RegularUser
        fields = ('username',
                  'email',
                  'password',
                  'rfid',
                  'telefono',
                  'avatar',
                  'descripcion',)

        widgets = {
            'telefono': PhoneNumberPrefixWidget(),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


### -------------- Admin User ---------------- ###

class AdminCreationForm(forms.ModelForm):
    """A form for creating new Admin users. Including all required fields,
    plus a repeated password"""
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repita Contraseña', widget=forms.PasswordInput)

    class Meta:
        model = AdminUser
        fields = ('username',
                  'email',
                  'password',
                  'telefono',
                  'avatar',
                  'usuarios',
                  'groups',)
        widgets = {
            'telefono': PhoneNumberPrefixWidget(),
        }

    def clean_password2(self):
        # Check that the 2 password entries match
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2


    def save(self, commit=True):
        # Save the commit password in hashed form
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        # Set the current User as admin user
        user.is_staff = True


        if commit:
            user.save()
        return user

    @receiver(post_save, sender= AdminUser)
    def add_admin_permission(sender, instance, created, **kwargs):
        if created:
            grupo = Group.objects.get(name="Administradores")
            grupo.user_set.add(instance)



class AdminChangeForm(forms.ModelForm):
    """ A form for updating Administrators. Includes all the fields on the user
    , but replaces the password field with admin's password hash display field"""

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = AdminUser
        fields = ('username',
                  'email',
                  'password',
                  'first_name',
                  'last_name',
                  'descripcion',
                  'telefono',
                  'avatar',
                  'usuarios',
                  'groups',
                  )
        widgets = {
            'telefono': PhoneNumberPrefixWidget(),
        }

    def clean_password(self):
        # Regardless of what the admin provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]