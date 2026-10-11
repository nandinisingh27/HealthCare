from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse

from healthcare.models import Doctor, Patient, PatientDoctorMapping
from .serializers import (
    LoginRequestSerializer,
    RegisterSerializer,
    DoctorSerializer,
    PatientSerializer,
    PatientDoctorMappingSerializer
)


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        summary="Log in user",
        description="Authenticate user with email and password to receive JWT tokens.",
        request=LoginRequestSerializer,
        responses={
            200: OpenApiResponse(description="Login successful, returns access & refresh tokens."),
            400: OpenApiResponse(description="Missing email or password."),
            401: OpenApiResponse(description="Invalid credentials.")
        },
        auth=[]
    )

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Both email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': {
                'id': user.id,
                'name': user.get_full_name() or user.first_name,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)


class PatientListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.doctor_mappings.all().delete()
        instance.delete()



class DoctorListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class MappingListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatientDoctorMappingSerializer

    def get_queryset(self):
        return PatientDoctorMapping.objects.select_related('patient', 'doctor').all()


class PatientDoctorMappingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get doctors for a patient",
        description="Retrieve all doctors assigned to a specific patient UUID.",
        responses={200: PatientDoctorMappingSerializer(many=True)}
    )
    def get(self, request, pk):
        patient = get_object_or_404(Patient, id=pk, user=request.user)
        mappings = PatientDoctorMapping.objects.filter(
            patient=patient,
            doctor__is_deleted=False
        ).select_related('doctor', 'patient')
        serializer = PatientDoctorMappingSerializer(
            mappings, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Remove doctor mapping",
        description="Delete a patient-doctor mapping record by its mapping UUID.",
        responses={204: OpenApiResponse(description="Doctor mapping deleted successfully.")}
    )
    def delete(self, request, pk):
        mapping = get_object_or_404(
            PatientDoctorMapping.objects.select_related('patient'),
            id=pk,
            patient__user=request.user
        )
        mapping.delete()
        return Response(
            {"detail": "Doctor mapping removed successfully."},
            status=status.HTTP_204_NO_CONTENT
        )