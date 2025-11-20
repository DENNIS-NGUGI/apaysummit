from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from .models import UserProfile, Participant, Invoice
import os


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text='A valid email address is required.'
    )
    company_name = forms.CharField(max_length=100, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'company_name', 'address', 'phone']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Basic email format validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError('Please enter a valid email address.')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered. Please use a different email.')
        
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Username validation
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Username can only contain letters, numbers, and underscores.')
        
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic phone number validation (Kenyan format)
            if not re.match(r'^\+?254\d{9}$|^0\d{9}$', phone):
                raise ValidationError('Please enter a valid Kenyan phone number (e.g., 0712345678 or +254712345678)')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            user_profile = user.userprofile
            user_profile.company_name = self.cleaned_data['company_name']
            user_profile.address = self.cleaned_data['address']
            user_profile.phone = self.cleaned_data['phone']
            user_profile.save()
        
        return user

class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError('Please enter a valid email address.')
        
        return email


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }

class MultipleParticipantForm(forms.Form):
    participants_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter participant details in this format:\nJohn Doe,john@email.com,0712345678\nJane Smith,jane@email.com,0723456789\n\nOne participant per line, separated by commas.',
            'rows': 10
        }),
        help_text='Format: Name,Email,Phone (one per line)'
    )

class AdminPaymentForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['status', 'payment_date', 'payment_reference']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction ID or Reference'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class ProofOfPaymentForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['proof_of_payment', 'payment_method', 'payment_notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'payment_notes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Enter payment reference or notes...'}),
            'proof_of_payment': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        }
    
    def clean_proof_of_payment(self):
        proof = self.cleaned_data.get('proof_of_payment')
        if proof:
            # Validate file type
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(proof.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    'Unsupported file type. Please upload PDF or image files (PDF, JPG, PNG, GIF).'
                )
            
            # Validate file size (5MB limit)
            if proof.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 5MB.')
        
        return proof

class AdminPaymentVerificationForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['status', 'payment_date', 'payment_reference']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter payment reference...'}),
        }

    def clean_proof_of_payment(self):
        proof = self.cleaned_data.get('proof_of_payment')
        if proof:
            # Validate file type
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(proof.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    'Unsupported file type. Please upload PDF or image files (PDF, JPG, PNG, GIF).'
                )
            
            # Validate file size (5MB limit)
            if proof.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 5MB.')
        
        return proof