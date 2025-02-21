from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from . import models

# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = models.CustomUser
    filter_horizontal = ()
    
    list_display = ('username','email','last_name','first_name','phone_number','address','account_status','verified')
    list_filter = ('account_status','is_staff','is_superuser','verified')
    search_fields = ('username','email','phone_number')

    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'phone_number', 'first_name', 'last_name', 'address')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Account Status', {
            'fields': ('account_status','verified')
        }),
    )

    def get_readonly_fields(self, request, obj = ...):
        """
        This method returns a list of fields that will be read-only in the admin.
        We want every field to be read-only except for 'account_status'.
        """
        # Get a list of all field names defined on the model
        all_fields = [field.name for field in self.model._meta.fields]
        # Allow only 'account_status' and 'verified' to be edited; everything else is read-only.
        readonly = [field for field in all_fields if field not in ['account_status', 'verified']]
        return readonly


admin.site.register(models.CustomUser,CustomUserAdmin)
admin.site.register(models.Make)
admin.site.register(models.Model)
admin.site.register(models.KeyFeatures)
admin.site.register(models.PartType)
admin.site.register(models.SubType)
admin.site.register(models.TypeOfService)
admin.site.register(models.SubTypeOfService)


