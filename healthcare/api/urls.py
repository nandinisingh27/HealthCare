from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    PatientListCreateView,
    PatientDetailView,
    DoctorListCreateView,
    DoctorDetailView,
    MappingListCreateView,
    PatientDoctorMappingDetailView
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),

    # Patients
    path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
    path('patients/<uuid:pk>/', PatientDetailView.as_view(), name='patient-detail'),

    # Doctors
    path('doctors/', DoctorListCreateView.as_view(), name='doctor-list-create'),
    path('doctors/<uuid:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),

    # Patient-Doctor Mappings
    path('mappings/', MappingListCreateView.as_view(), name='mapping-list-create'),
    path('mappings/<uuid:pk>/', PatientDoctorMappingDetailView.as_view(), name='mapping-detail-or-patient'),
]