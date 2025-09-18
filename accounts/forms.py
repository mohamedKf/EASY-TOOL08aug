from random import random

from django import forms
from django.contrib.auth import get_user_model
from .models import CustomUser, Project, Message, Company, MonthlyReport, MetalProfilePrice, DrywallBoardPrice, \
    DrywallBoard, MetalProfile, ProfileSet, Screw, Order
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, RegexValidator
from .models import Glass, Window, WindowFrame, WindowSash, Door, DoorFrame, DoorSash,Room
from .models import AluminumPrice, GlassPrice




class SignUpForm(forms.ModelForm):
    company_code = forms.CharField(required=False, label="Company Code")

    class Meta:
        model = CustomUser
        fields = ['name', 'username', 'email', 'phone', 'password', 'user_type']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make company code required for workers
        if self.data.get('user_type') == 'worker':
            self.fields['company_code'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    # ❌ Removed unique phone check
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')

        if user_type == 'worker':
            code = cleaned_data.get('company_code')
            try:
                company = Company.objects.get(code=code)
                cleaned_data['company'] = company
            except Company.DoesNotExist:
                self.add_error('company_code', "Invalid company code.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Set hashed password
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)

        # Assign company if found
        company = self.cleaned_data.get('company')
        if company:
            user.company = company

        if commit:
            user.save()

        return user


class RequestResetForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter your phone number",
                "class": "form-input"
            }
        )
    )

class VerifyResetForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'Code must be a 6-digit number')],
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter 6-digit code",
                "class": "form-input",
                "inputmode": "numeric",  # mobile keyboards show numbers
                "pattern": "[0-9]*"      # browsers enforce digits only
            }
        )
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "New Password", "class": "form-input"}
        )
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Confirm Password", "class": "form-input"}
        )
    )


User = get_user_model()
class CreateCompanyForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirm Your Password"
    )

    class Meta:
        model = Company
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CreateCompanyForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if self.user is None:
            raise forms.ValidationError("User is not provided.")

        password = cleaned_data.get("confirm_password")

        if not self.user.check_password(password):
            self.add_error('confirm_password', "Password confirmation failed.")

        if Company.objects.filter(contractor=self.user).exists():
            raise forms.ValidationError("You have already created a company.")

        return cleaned_data

    def save(self, commit=True):
        company = super().save(commit=False)
        company.contractor = self.user


        if commit:
            company.save()
            self.user.company = company
            self.user.save()

            # 🔁 Refresh user in form for re-login in view
            self.user = User.objects.get(pk=self.user.pk)


        return company


class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=None,  # Will be set dynamically in the view
        label="Send to",
        empty_label="Select recipient..."
    )

    class Meta:
        model = Message
        fields = ['recipient', 'text', 'image', 'file']

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filter recipients based on user's company
            if user.company:
                # Get all users from the same company (excluding the sender)
                same_company_users = CustomUser.objects.filter(
                    company=user.company
                ).exclude(id=user.id)

                self.fields['recipient'].queryset = same_company_users
            else:
                # If user has no company, show no recipients
                self.fields['recipient'].queryset = CustomUser.objects.none()

class LoginForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project_number', 'address', 'project_type', 'blueprints', 'workers']
        widgets = {
            'workers': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        contractor = kwargs.pop('contractor', None)
        super().__init__(*args, **kwargs)

        if contractor and contractor.company:
            self.fields['workers'].queryset = CustomUser.objects.filter(
                user_type='worker',
                company=contractor.company
            )
        else:
            self.fields['workers'].queryset = CustomUser.objects.none()

        self.fields['workers'].required = False  # <-- This makes it optional

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'blueprint']

class GlassForm(forms.ModelForm):
    class Meta:
        model = Glass
        fields = ['width', 'height', 'glass_type', 'price']
        widgets = {
            'glass_type': forms.Select(choices=Glass.GLASS_TYPES),
        }

class WindowForm(forms.ModelForm):
    class Meta:
        model = Window
        fields = ['window_number', 'window_type', 'number_of_sashs', 'aluminum_type', 'project']
        widgets = {
            'window_type': forms.Select(choices=Window.WINDOW_TYPES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Default: all types shown
        self.fields['aluminum_type'].choices = (
            Window.SLIDING_ALUMINUM_TYPES + Window.MULTI_BOLT_ALUMINUM_TYPES
        )

        # Optional: filter if instance has window_type set
        window_type = self.initial.get('window_type') or self.data.get('window_type') or self.instance.window_type
        if window_type == 'sliding':
            self.fields['aluminum_type'].choices = Window.SLIDING_ALUMINUM_TYPES
        elif window_type == 'multi_bolt':
            self.fields['aluminum_type'].choices = Window.MULTI_BOLT_ALUMINUM_TYPES


    def get_aluminum_types(self):
        # Return the appropriate aluminum types based on the window type
        if self.instance.window_type == 'sliding':
            return Window.SLIDING_ALUMINUM_TYPES
        elif self.instance.window_type == 'multi_bolt':
            return Window.MULTI_BOLT_ALUMINUM_TYPES
        return []


class WindowFrameForm(forms.ModelForm):
    class Meta:
        model = WindowFrame
        fields = ['side', 'top', 'bottom']


class WindowSashForm(forms.ModelForm):
    class Meta:
        model = WindowSash
        fields = ['side', 'top', 'bottom', 'glass']

class DoorForm(forms.ModelForm):
    class Meta:
        model = Door
        fields = ['door_number', 'door_type', 'number_of_sashs', 'aluminum_type', 'project']
        widgets = {
            'door_type': forms.Select(choices=Door.DOOR_TYPES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['aluminum_type'].choices = (
            Door.SLIDING_ALUMINUM_TYPES + Door.MULTI_BOLT_ALUMINUM_TYPES
        )

        door_type = self.initial.get('door_type') or self.data.get('door_type') or self.instance.door_type
        if door_type == 'sliding':
            self.fields['aluminum_type'].choices = Door.SLIDING_ALUMINUM_TYPES
        elif door_type == 'multi_bolt':
            self.fields['aluminum_type'].choices = Door.MULTI_BOLT_ALUMINUM_TYPES

    def get_aluminum_types(self):
        # Return the appropriate aluminum types based on the door type
        if self.instance.door_type == 'sliding':
            return Door.SLIDING_ALUMINUM_TYPES
        elif self.instance.door_type == 'multi_bolt':
            return Door.MULTI_BOLT_ALUMINUM_TYPES
        return []


class DoorFrameForm(forms.ModelForm):
    class Meta:
        model = DoorFrame
        fields = ['side', 'top']



class DoorSashForm(forms.ModelForm):
    class Meta:
        model = DoorSash
        fields = ['side', 'top', 'bottom', 'glass']


class AluminumPriceForm(forms.ModelForm):
    class Meta:
        model = AluminumPrice
        fields = ['aluminum_type', 'price_per_m2']
        widgets = {
            'aluminum_type': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

class GlassPriceForm(forms.ModelForm):
    class Meta:
        model = GlassPrice
        fields = ['glass_type', 'price_per_m2']
        widgets = {
            'glass_type': forms.HiddenInput(),
            'price_per_m2': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure value is submitted even though disabled
        self.fields['glass_type'].disabled = False


class DrywallBoardPriceForm(forms.ModelForm):
    class Meta:
        model = DrywallBoardPrice
        fields = ['color', 'size', 'price_per_board']
        widgets = {
            'color': forms.Select(choices=[
                ('green', 'Green'),
                ('blue', 'Blue'),
                ('white', 'White'),
                ('pink', 'Pink'),
            ]),
            'size': forms.Select(choices=[
                ('200x120', '200x120'),
                ('260x120', '260x120'),
                ('300x120', '300x120'),
            ]),
            'price_per_board': forms.NumberInput(attrs={'step': '0.01'}),
        }

class MetalProfilePriceForm(forms.ModelForm):
    class Meta:
        model = MetalProfilePrice
        fields = ['profile_type', 'thickness', 'price_per_meter']
        widgets = {
            'profile_type': forms.Select(choices=[
                ('stud', 'Stud'),
                ('track', 'Track')
            ]),
            'thickness': forms.Select(choices=[
                ('37', '37 mm'),
                ('50', '50 mm'),
                ('70', '70 mm'),
                ('F47', 'F47')
            ])
        }


class PayrollUploadForm(forms.ModelForm):
    class Meta:
        model = MonthlyReport
        fields = ['payroll_file']


class AluminumItemForm(forms.Form):
    ITEM_TYPE_CHOICES = [
        ('window', 'Window'),
        ('door', 'Door'),
    ]

    item_type = forms.ChoiceField(choices=ITEM_TYPE_CHOICES)
    subtype = forms.CharField(max_length=50)
    aluminum_type = forms.CharField(max_length=20)
    glass_type = forms.CharField(max_length=50)

    height_left = forms.FloatField()
    height_middle = forms.FloatField()
    height_right = forms.FloatField()

    width_top = forms.FloatField()
    width_middle = forms.FloatField()
    width_bottom = forms.FloatField()

class ScrewForm(forms.ModelForm):
    class Meta:
        model = Screw
        exclude = ['supplier', 'date_added']
        widgets = {
            'length_cm': forms.Select(),
            'screw_type': forms.Select(),
            'count_per_box': forms.Select(),
        }


class ProfileSetForm(forms.ModelForm):
    ALUMINUM_TYPES = [
        ('1700', '1700'),
        ('7000', '7000'),
        ('7300', '7300'),
        ('9000', '9000'),
        ('9200', '9200'),
        ('4400', '4400'),
        ('4300', '4300'),
        ('4500', '4500'),
        ('9400', '9400'),
        ('2200', '2200'),
        ('2000', '2000'),
    ]

    # Override the field to make it a dropdown
    aluminum_type = forms.ChoiceField(
        choices=ALUMINUM_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Aluminum Profile Type"
    )

    class Meta:
        model = ProfileSet
        fields = ['name', 'aluminum_type', 'kind', 'weight_per_meter', 'price_per_kilo']

class MetalProfileForm(forms.ModelForm):
    class Meta:
        model = MetalProfile
        exclude = ['supplier', 'date_added']
        widgets = {
            'profile_type': forms.Select(),
            'size': forms.Select(),
        }


class DrywallBoardForm(forms.ModelForm):
    class Meta:
        model = DrywallBoard
        exclude = ['supplier', 'date_added']
        widgets = {
            'color': forms.Select(),
            'size': forms.Select(),
        }

class OrderStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(choices=[
                ('approved', 'Approved'),
                ('completed', 'Completed'),
            ])
        }


class DeliveryDateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['delivery_date']
        widgets = {
            'delivery_date': forms.DateInput(attrs={'type': 'date'})
        }