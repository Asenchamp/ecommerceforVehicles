from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .forms import UsersCreationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Vehicle, Model, SparePart, SubType, Service, TypeOfService, SubTypeOfService, Image, ServiceSubTypeOfService, Make
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import UserUpdateForm, VehicleForm, SparePartForm, ServicesForm, EmailForm, OTPVerificationForm
from django.http import JsonResponse
from django.views.generic.list import ListView
from django.views.generic import TemplateView, DetailView
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.generic.edit import FormView
import random
from django.core.mail import  send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q, Case, When, BooleanField
from PIL import Image as PILImage
import io
import os


class landing_page(TemplateView):
    template_name = 'landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Search and Filter Logic
        search_query = self.request.GET.get('search', '')
        vehicle_filter = self.request.GET.get('vehicle_filter', '')
        sparepart_filter = self.request.GET.get('sparepart_filter', '')
        service_filter = self.request.GET.get('service_filter', '')

        #ordering data by verified status
        verified_ordering = Case(
            When(user__verified=True, then=True),
            default=False,
            output_field=BooleanField(),
        )


        # Vehicles
        vehicles = Vehicle.objects.all().select_related('user').prefetch_related('key_features').order_by('-user__verified')
        spareparts = SparePart.objects.all().select_related('user').order_by('-user__verified')
        services = Service.objects.all().select_related('user').prefetch_related('sub_services').order_by('-user__verified')


        if search_query:            
            vehicles = vehicles.filter(Q(make__name__icontains=search_query) | Q(description__icontains=search_query))
            spareparts = spareparts.filter(Q(type__name__icontains=search_query) | Q(description__icontains=search_query))
            services = services.filter(Q(type_of_service__name__icontains=search_query) | Q(description__icontains=search_query))


        if vehicle_filter:   
            if vehicle_filter == 'All':
                vehicles = vehicles
            else:
                vehicles = vehicles.filter(make__name__icontains=vehicle_filter)  
            spareparts = SparePart.objects.none()
            services = Service.objects.none()          
        if sparepart_filter:   
            if sparepart_filter == 'All':
                spareparts = spareparts
            else:
                spareparts = spareparts.filter(type__name__icontains=sparepart_filter)   
            vehicles = Vehicle.objects.none()
            services = Service.objects.none()         
        if service_filter:            
            if service_filter == 'All':
                services = services
            else:
                services = services.filter(type_of_service__name__icontains=service_filter)
            vehicles = Vehicle.objects.none()
            spareparts = SparePart.objects.none()

                                    
        context['vehicles'] = vehicles
        context['spareparts'] = spareparts
        context['services'] = services
        
        # Rest of your existing logic for images
        # vehicle_ids = [v.id for v in vehicles]
        # Vehicle_images = Image.objects.filter(entity_type='Vehicle', entity_id__in=vehicle_ids)
        # images_by_vehicleId = {}
        # for img in Vehicle_images:
        #     images_by_vehicleId.setdefault(img.entity_id, []).append(img)
        # context['images_by_vehicleId'] = images_by_vehicleId

        # spareparts_ids = [sp.id for sp in spareparts]
        # spareparts_images = Image.objects.filter(entity_type='Spareparts', entity_id__in=spareparts_ids)
        # images_by_sparepartId = {}
        # for img in spareparts_images:
        #     images_by_sparepartId.setdefault(img.entity_id, []).append(img)
        # context['images_by_sparepartId'] = images_by_sparepartId

        # service_ids = [s.id for s in services]
        # Service_images = Image.objects.filter(entity_type='Service', entity_id__in=service_ids)
        # images_by_serviceId = {}
        # for img in Service_images:
        #     images_by_serviceId.setdefault(img.entity_id, []).append(img)
        # context['images_by_serviceId'] = images_by_serviceId

        # Fetch only the first image for each entity
        context['vehicle_images'] = {v.id: Image.objects.filter(entity_type='Vehicle', entity_id=v.id).first() or None for v in vehicles}
        context['spareparts_images'] = {sp.id: Image.objects.filter(entity_type='Spareparts', entity_id=sp.id).first() or None for sp in spareparts}
        context['service_images'] = {s.id: Image.objects.filter(entity_type='Service', entity_id=s.id).first() or None for s in services}



        # Add search and filter parameters to context for form repopulation
        context['search_query'] = search_query
        context['vehicle_filter'] = vehicle_filter
        context['sparepart_filter'] = sparepart_filter
        context['service_filter'] = service_filter

        return context

# -- otp Email View ---
class OTPEmailView(FormView):
    template_name = 'accounts/otp_email.html'
    form_class = EmailForm
    success_url = reverse_lazy('otp-verify')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        #generate a 6-digit otp
        otp = str(random.randint(100000, 999999))
        #store the otp and email in session
        self.request.session['signup_otp'] = otp
        self.request.session['signup_email'] = email
        #send the otp via email
        send_mail(
            subject="YOUR OTP CODE",
            message=f"Your OTP code is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return super().form_valid(form)

class OTPVerifyView(FormView):
    template_name = 'accounts/otp_verify.html'
    form_class = OTPVerificationForm
    success_url = reverse_lazy('register')

    def form_valid(self, form):
        user_otp = form.cleaned_data['otp']
        session_otp = self.request.session.get('signup_otp')
        print(f"User OTP: {user_otp}")
        print(f"Session OTP: {session_otp}")
        if user_otp == session_otp:
            #mark otp as verified in session 
            self.request.session['otp_verified'] = True
            print(f"OTP Verified: {self.request.session.get('otp_verified')}")
            return super().form_valid(form)
        else:
            form.add_error('otp', "Incorect OTP, please try again")
            return super().form_valid(form)

# -- site registration view -- 
class RegisterView(CreateView):
    form_class = UsersCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs.update({'request': self.request})
    #     return kwargs

    # def form_valid(self, form):
    #     form.save(self.request)
    #     return super().form_valid(form)

# --login view -- 
def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        print('password: ', password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('landing')
        else:
            messages.error(request,'Invalid username or password')
    return render(request, 'registration/login.html')

# --- update profile --
class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = UserUpdateForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('dashboard')
    def test_func(self):
        User = self.get_object()
        return self.request.user.id == User.id
    def get_object(self, queryset=None):
        return self.request.user
    def form_valid(self, form):
        response = super().form_valid(form)
        uploaded_file = self.request.FILES.get('profile_picture')
        if uploaded_file:
            #Enforcing one pic and deleting existing ones
            Image.objects.filter(
                entity_type = 'Users',
                entity_id = self.object.id
            ).delete()
            file_path = default_storage.save(f"profile_pictures/{uploaded_file.name}",
                                             ContentFile(uploaded_file.read()))
            Image.objects.create(
                image_path = file_path,
                entity_type='Users',
                entity_id = self.object.id
            )
        return response
      

# -- landing page after login --
class dashboard(LoginRequiredMixin, ListView):
    model = Vehicle
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vehicles = Vehicle.objects.filter(user = self.request.user).prefetch_related('key_features')
        spareparts = SparePart.objects.filter(user = self.request.user)
        services = Service.objects.filter(user = self.request.user).prefetch_related('sub_services')

        context['vehicles'] = vehicles
        context['spareparts'] = spareparts
        context['services'] = services

        # Fetch only the first image for each entity
        context['vehicle_images'] = {v.id: Image.objects.filter(entity_type='Vehicle', entity_id=v.id).first() or None for v in vehicles}
        context['spareparts_images'] = {sp.id: Image.objects.filter(entity_type='Spareparts', entity_id=sp.id).first() or None for sp in spareparts}
        context['service_images'] = {s.id: Image.objects.filter(entity_type='Service', entity_id=s.id).first() or None for s in services}

        return context

        # #extract all vehicle IDS
        # vehicle_ids = [v.id for v in vehicles]
        # #fetch images for these vehicle IDS
        # Vehicle_images = Image.objects.filter(
        #     entity_type = 'Vehicle',
        #     entity_id__in = vehicle_ids
        # )
        # #group images by vehicle ID
        # images_by_vehicleId = {}
        # for img in Vehicle_images:
        #     images_by_vehicleId.setdefault(img.entity_id, []).append(img)
        # context['images_by_vehicleId'] = images_by_vehicleId

        # #extract all sparepart IDS
        # spareparts_ids = [sp.id for sp in spareparts]
        # #fetch images for these sparepart IDS
        # spareparts_images = Image.objects.filter(
        #     entity_type = 'Spareparts',
        #     entity_id__in = spareparts_ids
        # )
        # #group images by sparepart ID
        # images_by_sparepartId = {}
        # for img in spareparts_images:
        #     images_by_sparepartId.setdefault(img.entity_id, []).append(img)
        # context['images_by_sparepartId'] = images_by_sparepartId
        # #extract all service IDS
        # service_ids = [s.id for s in services]
        # #fetch images for these service IDS
        # Service_images = Image.objects.filter(
        #     entity_type = 'Service',
        #     entity_id__in = service_ids
        # )
        # #group images by service ID
        # images_by_serviceId = {}
        # for img in Service_images:
        #     images_by_serviceId.setdefault(img.entity_id, []).append(img)
        # context['images_by_serviceId'] = images_by_serviceId

        # return context

# -- mixin to handle images ---
class ImageHandlingMixin:
    def handle_images(self, form, entity__type, entity__id):
        #handle file uploads for images
        images = self.request.FILES.getlist('images')
        for img in images:
            #open image using pillow
            pil_image = PILImage.open(img)
            #save to a BytesIO object for webpconversion
            img_io = io.BytesIO()
            #convert to webp
            pil_image.save(img_io, format="WEBP", quality=85)
            img_io.seek(0)
            # generate new file name with .webp
            new_filename = f"{os.path.splitext(img.name)[0]}.webp"
            #save the image to media root using django default storage
            img_path = default_storage.save(f"{entity__type.lower()}_images/{new_filename}", ContentFile(img_io.getvalue()))
            #craete an image object using the the polymorphiv image model
            Image.objects.create(
                image_path = img_path,
                entity_type = entity__type,
                entity_id = entity__id
            )
            print("Saved: ", img_path)

    def images_to_delete(self, form, entity__type, entity__id):
        # Handle image deletions
        images_to_delete = self.request.POST.getlist('delete_images')
        for img_id in images_to_delete:
            try:
                img = Image.objects.get(id=img_id, entity_type=entity__type, entity_id=entity__id)
                img.delete()
            except Image.DoesNotExist:
                pass  # Handle the case where the image might not exist

# view for creaating vehicles
class VehicleCreateView(LoginRequiredMixin, CreateView, ImageHandlingMixin):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        # auto assign the vehicle to the logged in user
        form.instance.user = self.request.user
        response = super().form_valid(form) #save the vehicle first
        #set key features many-to-may field
        form.instance.key_features.set(form.cleaned_data.get('key_features'))
        #handle images with the mixin
        self.handle_images(form, 'Vehicle', self.object.id)

        return response

# --- update existing vehicle and this done by the owner ----
class VehicleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView, ImageHandlingMixin):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        vehicle = self.get_object()
        return self.request.user == vehicle.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch images for this vehicle
        vehicle_images = Image.objects.filter(entity_type='Vehicle', entity_id=self.object.id)
        context['vehicle_images'] = vehicle_images
        return context
    
    def form_valid(self, form):
        # Set key features
        form.instance.key_features.set(form.cleaned_data.get('key_features'))

        #handle images with the mixin
        self.handle_images(form, 'Vehicle', self.object.id)

        self.images_to_delete(form, 'Vehicle', self.object.id)

        return super().form_valid(form)
    
# --- deleting vehicle ---
class VehicleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Vehicle
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        vehicle = self.get_object()
        return self.request.user == vehicle.user

    # Override GET to bypass the confirmation page
    def get(self, request, *args, **kwargs):
        # Call the post method to delete immediately on GET request.
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.success_url)
    
# view to return json response of the models for a selected make
def load_models(request):
    make_id = request.GET.get('make')
    if make_id:
        model_qs = Model.objects.filter(make_id = make_id).order_by('name')
        model_list = list(model_qs.values('id','name'))
        return JsonResponse({"models": model_list}, safe=False)
    return JsonResponse({"models":[]}, safe=False)


def load_makes(request):
    makes = Make.objects.values('id', 'name')  # Fetch all makes
    return JsonResponse({"makes": list(makes)})


# --- create the spare part --- 
class SparepartCreateView(LoginRequiredMixin, CreateView, ImageHandlingMixin):
    model = SparePart
    form_class = SparePartForm
    template_name = 'spareparts/sparepart_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user

        response = super().form_valid(form)

        #handle images with the mixin
        self.handle_images(form, 'Spareparts', self.object.id)

        return response
    
# --- update existing sparepart and this done by the owner ----
class SparepartUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView, ImageHandlingMixin):
    model = SparePart
    form_class = SparePartForm
    template_name = 'spareparts/sparepart_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        sparePart = self.get_object()
        return self.request.user == sparePart.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch images for this sparepart
        spareparts_images = Image.objects.filter(entity_type='Spareparts', entity_id=self.object.id)
        context['spareparts_images'] = spareparts_images
        return context
    
    def form_valid(self, form):
        #handle images with the mixin
        self.handle_images(form, 'Spareparts', self.object.id)

        self.images_to_delete(form, 'Spareparts', self.object.id)
        return super().form_valid(form)
    
# --- deleting sparepart ---
class SparepartDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SparePart
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        sparePart = self.get_object()
        return self.request.user == sparePart.user

    # Override GET to bypass the confirmation page
    def get(self, request, *args, **kwargs):
        # Call the post method to delete immediately on GET request.
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.success_url)
        
# return json response for subtypes of the selected type ---
def load_subtypes(request):
    type_id = request.GET.get('type')
    if type_id:
        subtype_qs = SubType.objects.filter(type_id = type_id).order_by('name')
        subtype_list = list(subtype_qs.values('id','name'))
        return JsonResponse({"subtype": subtype_list}, safe=False)
    return JsonResponse({"subtype": []}, safe=False)

# --- create services -----
class ServiceCreateView(LoginRequiredMixin, CreateView, ImageHandlingMixin):
    model = Service
    form_class = ServicesForm
    template_name = 'services/services_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form) # save the service first
        #set key features many-to-may field
        form.instance.sub_services.set(form.cleaned_data.get('sub_services'))
        #handle images with the mixin
        self.handle_images(form, 'Service', self.object.id)
        return response

# --- update existing vehicle and this done by the owner ----
class ServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView, ImageHandlingMixin):
    model = Service
    form_class = ServicesForm
    template_name = 'services/services_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        service = self.get_object()
        return self.request.user == service.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch images for this sparepart
        services_images = Image.objects.filter(entity_type='Service', entity_id=self.object.id)
        context['services_images'] = services_images
        return context
    
    def form_valid(self, form):
        form.instance.sub_services.set(form.cleaned_data.get('sub_services'))
        #handle images with the mixin
        self.handle_images(form, 'Service', self.object.id)
        self.images_to_delete(form, 'Service', self.object.id)
        return super().form_valid(form)

# --- deleting service ---
class ServiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Service
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        service = self.get_object()
        return self.request.user == service.user

    # Override GET to bypass the confirmation page
    def get(self, request, *args, **kwargs):
        # Call the post method to delete immediately on GET request.
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.success_url)
    
def load_subtypeofservice(request):
    type_of_service_id = request.GET.get('type_of_service')
    if type_of_service_id:
        sub_services_qs = SubTypeOfService.objects.filter(type_of_service_id = type_of_service_id).order_by('name')
        sub_services_list = list(sub_services_qs.values('id','name'))
        return JsonResponse({"sub_services": sub_services_list}, safe=False)
    return JsonResponse({"sub_services":[]}, safe=False)


class VehicleDetailView(DetailView):
    model = Vehicle
    template_name = 'vehicles/vehicle_detail.html'
    context_object_name = 'vehicle'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch all images for the vehicle
        vehicle_images = Image.objects.filter(
            entity_type='Vehicle',
            entity_id=self.object.id
        ).all()  # Use .all() to get all images
        context['vehicle_images'] = vehicle_images  # List of all images or empty queryset

        # Fetch related vehicles (same make), ordered by user__verified
        context['related_vehicles'] = Vehicle.objects.filter(
            make=self.object.make
        ).exclude(id=self.object.id).annotate(
            verified_order=Case(
                When(user__verified=True, then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).order_by('-verified_order')[:5]  # Limit to 5 related items

        # Fetch one image for each related vehicle
        related_vehicle_ids = [v.id for v in context['related_vehicles']]
        related_vehicle_images = {}
        if related_vehicle_ids:
            related_vehicle_images = {
                v.id: Image.objects.filter(
                    entity_type='Vehicle',
                    entity_id=v.id
                ).first() for v in context['related_vehicles']
            }
        context['related_vehicle_images'] = related_vehicle_images

        return context
    

class SparePartDetailView(DetailView):
    model = SparePart
    template_name = 'spareparts/sparepart_detail.html'
    context_object_name = 'sparepart'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch all images for the spare part
        sparepart_images = Image.objects.filter(
            entity_type='Spareparts',
            entity_id=self.object.id
        ).all()  # Use .all() to get all images
        context['sparepart_images'] = sparepart_images  # List of all images or empty queryset

        # Fetch related spare parts (same type), ordered by user__verified
        context['related_spareparts'] = SparePart.objects.filter(
            type=self.object.type  # Adjust field as needed based on your model
        ).exclude(id=self.object.id).annotate(
            verified_order=Case(
                When(user__verified=True, then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).order_by('-verified_order')[:5]

        # Fetch one image for each related spare part
        related_sparepart_ids = [sp.id for sp in context['related_spareparts']]
        related_sparepart_images = {}
        if related_sparepart_ids:
            related_sparepart_images = {
                sp.id: Image.objects.filter(
                    entity_type='Spareparts',
                    entity_id=sp.id
                ).first() for sp in context['related_spareparts']
            }
        context['related_sparepart_images'] = related_sparepart_images

        return context
    
class ServiceDetailView(DetailView):
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch all images for the service
        service_images = Image.objects.filter(
            entity_type='Service',
            entity_id=self.object.id
        ).all()  # Use .all() to get all images
        context['service_images'] = service_images  # List of all images or empty queryset

        # Fetch related services (same type_of_service), ordered by user__verified
        context['related_services'] = Service.objects.filter(
            type_of_service=self.object.type_of_service
        ).exclude(id=self.object.id).annotate(
            verified_order=Case(
                When(user__verified=True, then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).order_by('-verified_order')[:5]

        # Fetch one image for each related service
        related_service_ids = [s.id for s in context['related_services']]
        related_service_images = {}
        if related_service_ids:
            related_service_images = {
                s.id: Image.objects.filter(
                    entity_type='Service',
                    entity_id=s.id
                ).first() for s in context['related_services']
            }
        context['related_service_images'] = related_service_images

        return context


class UserListingsView(TemplateView):
    template_name = 'accounts/user_listings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the user id from URL kwargs, e.g., /user/<pk>/listings/
        user_id = self.kwargs.get('pk')
        target_user = get_object_or_404(CustomUser, id=user_id)
        context['target_user'] = target_user

        # Filter listings for this user
        vehicles = Vehicle.objects.filter(user=target_user).prefetch_related('key_features')
        spareparts = SparePart.objects.filter(user=target_user)
        services = Service.objects.filter(user=target_user).prefetch_related('sub_services')
        users = CustomUser.objects.filter(id=user_id)

        context['vehicles'] = vehicles
        context['spareparts'] = spareparts
        context['services'] = services
        context['users'] = users

        #fetching profile image
        context['profile_image'] = {
            p.id: Image.objects.filter(entity_type='Users', entity_id=p.id).first() for p in users
        }

        # For each listing, fetch only the first image (if any)
        context['vehicle_images'] = {
            v.id: Image.objects.filter(entity_type='Vehicle', entity_id=v.id).first() for v in vehicles
        }
        context['spareparts_images'] = {
            sp.id: Image.objects.filter(entity_type='Spareparts', entity_id=sp.id).first() for sp in spareparts
        }
        context['service_images'] = {
            s.id: Image.objects.filter(entity_type='Service', entity_id=s.id).first() for s in services
        }
        
        return context





