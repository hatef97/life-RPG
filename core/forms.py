from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import MentalCheckIn, Reflection
from .services import today


class SignupForm(UserCreationForm):
    display_name = forms.CharField(label="نام نمایشی", max_length=120, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "display_name", "password1", "password2")


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="نام کاربری")
    password = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)


class GiftAmountForm(forms.Form):
    amount = forms.CharField(
        label="مبلغ (تومان)",
        widget=forms.TextInput(attrs={
            "class": "control-input gift-amount-input",
            "placeholder": "مثال: 5,000,000",
            "inputmode": "numeric",
            "autocomplete": "off",
            "dir": "ltr",
        }),
    )

    def clean_amount(self):
        raw = self.cleaned_data.get("amount", "")
        cleaned = raw.replace(",", "").strip()
        try:
            value = Decimal(cleaned)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("مبلغ وارد شده معتبر نیست.")
        if value <= 0:
            raise forms.ValidationError("مبلغ باید بیشتر از صفر باشد.")
        return value / Decimal("1000000")


class MentalCheckInForm(forms.ModelForm):
    date = forms.DateField(
        label="تاریخ",
        initial=today,
        widget=forms.DateInput(attrs={"type": "date", "class": "control-input"}),
    )

    class Meta:
        model = MentalCheckIn
        fields = ("date", "energy", "focus", "mood", "motivation", "stress", "control")
        labels = {
            "energy": "Energy",
            "focus": "Focus",
            "mood": "Mood",
            "motivation": "Motivation",
            "stress": "Stress",
            "control": "Control",
        }
        widgets = {
            field: forms.NumberInput(attrs={"type": "range", "min": "1", "max": "10", "class": "range-input"})
            for field in ["energy", "focus", "mood", "motivation", "stress", "control"]
        }


class ReflectionForm(forms.ModelForm):
    date = forms.DateField(
        label="تاریخ",
        initial=today,
        widget=forms.DateInput(attrs={"type": "date", "class": "control-input"}),
    )

    class Meta:
        model = Reflection
        fields = ("date", "text")
        labels = {"text": "Reflection"}
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "control-textarea",
                    "placeholder": "۳ خط درباره امروز: چه چیزی برد بود؟ چه چیزی باید اصلاح شود؟ قدم بعدی چیست؟",
                }
            )
        }
