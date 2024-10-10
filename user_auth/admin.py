from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

class CustomUserCreationForm(forms.ModelForm):
    """
    A form for creating new users. Includes all required fields, plus a repeated password.
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'is_verified')

    def clean_password2(self):
        # Check that the two password entries match.
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format.
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    """
    A form for updating users. Excludes non-editable fields.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'password', 'is_active', 'is_staff', 'is_superuser',
            'is_verified', 'groups', 'user_permissions'
        )

class CustomUserAdmin(UserAdmin):
    # Use the custom forms
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    # List view
    list_display = (
        'username', 'email', 'is_staff', 'is_active', 'is_verified',
        'created_on', 'updated_on'
    )
    list_filter = ('is_staff', 'is_active', 'is_verified')

    # Fieldsets for detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email',)}),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_verified',
                'groups', 'user_permissions'
            )
        }),
        ('Important Dates', {'fields': ('last_login', 'created_on', 'updated_on')}),
    )

    # Fields for add user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_verified', 'is_staff', 'is_active')}
         ),
    )

    # Read-only fields
    readonly_fields = ('created_on', 'updated_on')
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
