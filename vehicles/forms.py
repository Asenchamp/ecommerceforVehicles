from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Vehicle, Make, Model, KeyFeatures, SparePart, PartType, SubType, Service, SubTypeOfService
from django import forms
from allauth.account.forms import SignupForm

class UsersCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username','email','last_name','first_name','phone_number','address')

# class UsersCreationForm(SignupForm):
#     # Add custom fields
#     phone_number = forms.CharField(max_length=14, required=True)
#     address = forms.CharField(max_length=50, required=True)
#     last_name = forms.CharField(max_length=150, required=True)
#     first_name = forms.CharField(max_length=150, required=True)

#     def __init__(self, *args, **kwargs):
#         self.request = kwargs.pop('request', None)  # grab the request to access session
#         super().__init__(*args, **kwargs)
#         # Add custom fields to the form if they're not automatically included by SignupForm
#         self.fields['phone_number'] = forms.CharField(max_length=14, required=True)
#         self.fields['address'] = forms.CharField(max_length=50, required=True)
#         self.fields['last_name'] = forms.CharField(max_length=150, required=True)
#         self.fields['first_name'] = forms.CharField(max_length=150, required=True)

#     def clean(self):
#         cleaned_data = super().clean()
#         if not self.request or not self.request.session.get('otp_verified'):
#             raise forms.ValidationError("You must verify your email first")
#         return cleaned_data

#     def save(self, request):
#         # Save the user with allauth's method
#         user = super().save(request)
#         # Update the user with session email and custom fields
#         session_email = request.session.get('signup_email')
#         if session_email:
#             user.email = session_email
        
#         # Set custom fields
#         user.phone_number = self.cleaned_data.get('phone_number')
#         user.address = self.cleaned_data.get('address')
#         user.last_name = self.cleaned_data.get('last_name')
#         user.first_name = self.cleaned_data.get('first_name')
        
#         user.save()
        
#         # Clean up session variables
#         for key in ['signup_otp', 'otp_verified', 'signup_email']:
#             if key in request.session:
#                 del request.session[key]
        
#         return user

class UserUpdateForm(forms.ModelForm):
    profile_picture = forms.FileField(required=False, label="Profile Picture")
    class Meta:
        model = CustomUser
        fields = ('username','email','last_name','first_name','phone_number','address')


class  VehicleForm(forms.ModelForm):

    key_features = forms.ModelMultipleChoiceField(
        queryset=KeyFeatures.objects.all(),
        required = False,
        widget = forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Vehicle
        fields = ['make','model','year','color','interior_color','condition',
                  'transmission','description','for_sale_or_rent','price','rate','fuel_type']
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            #initially load no models
            self.fields['model'].queryset = Model.objects.none()

            if 'make' in self.data:
                try:
                    make_id = int(self.data.get('make'))
                    self.fields['model'].queryset = Model.objects.filter(make_id = make_id).order_by('name')
                except(ValueError,TypeError):
                    pass  # when input is invalid, fallback to empty query set
            elif self.instance.pk:
                # when editing an existing vehicle, load the models for the selected make
                self.fields['model'].queryset = self.instance.make.model_set.order_by('name')


class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = ['title','make','model','type','subtype','condition','description','price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #initially load no models
        self.fields['model'].queryset = Model.objects.none()
        self.fields['subtype'].queryset = SubType.objects.none()

        if 'make' or 'type' in self.data:
            try:
                make_id = int(self.data.get('make'))
                self.fields['model'].queryset = Model.objects.filter(make_id = make_id).order_by('name')
                type_id = int(self.data.get('type'))
                self.fields['subtype'].queryset = SubType.objects.filter(type_id = type_id).order_by('name')
            except(ValueError,TypeError):
                pass  # when input is invalid, fallback to empty query set
        elif self.instance.pk:
            # when editing an existing vehicle, load the models for the selected make
            self.fields['model'].queryset = self.instance.make.model_set.order_by('name')
            self.fields['subtype'].queryset = self.instance.type.subtype_set.order_by('name')

class ServicesForm(forms.ModelForm):
    sub_services = forms.ModelMultipleChoiceField(
        queryset= SubTypeOfService.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Service
        fields = ['type_of_service','sub_services','description','start_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_services'].queryset = SubTypeOfService.objects.none()

        if 'type_of_service' in self.data:
            try:
                type_of_service_id = int(self.data.get('type_of_service'))
                self.fields['sub_services'].queryset = SubTypeOfService.objects.filter(type_of_service_id = type_of_service_id).order_by('name')
            except(ValueError,TypeError):
                pass
        elif self.instance.pk:
            self.fields['sub_services'].queryset = self.instance.type_of_service.subtypeofservice_set.order_by('name')

#-- otp forms --- 
class EmailForm(forms.Form):
    email = forms.EmailField(label="Enter your Email")
    
class OTPVerificationForm(forms.Form):
    otp = forms.CharField(label="Enter OTP", max_length=6,
                          help_text="Check your Email for the one-time password.")






