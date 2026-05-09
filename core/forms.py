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
    amount = forms.DecimalField(
        label="مبلغ به میلیون",
        min_value=0.01,
        max_digits=8,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.25", "class": "control-input"}),
    )


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
