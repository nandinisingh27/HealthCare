import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)

    def restore(self):
        return self.update(is_deleted=False, deleted_at=None)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])


phone_validator = RegexValidator(
    regex=r'^(?:\+91|91|0)?[6-9]\d{9}$',
    message="Enter a valid Indian phone number (e.g. '+919876543210' or '9876543210')."
)


class Doctor(BaseModel):
    class SpecializationChoices(models.TextChoices):
        CARDIOLOGY = 'Cardiology', 'Cardiology'
        DERMATOLOGY = 'Dermatology', 'Dermatology'
        NEUROLOGY = 'Neurology', 'Neurology'
        PEDIATRICS = 'Pediatrics', 'Pediatrics'
        ORTHOPEDICS = 'Orthopedics', 'Orthopedics'
        GENERAL = 'General Practice', 'General Practice'
        ONCOLOGY = 'Oncology', 'Oncology'

    name = models.CharField(max_length=150, db_index=True)
    specialization = models.CharField(
        max_length=64,
        choices=SpecializationChoices.choices,
        default=SpecializationChoices.GENERAL
    )
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(validators=[phone_validator], max_length=20)

    class Meta(BaseModel.Meta):
        db_table = 'doctor'


class Patient(BaseModel):
    class GenderChoices(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'
        OTHER = 'Other', 'Other'

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='patients'
    )
    name = models.CharField(max_length=150, db_index=True)
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(150)]
    )
    gender = models.CharField(max_length=10, choices=GenderChoices.choices)
    medical_history = models.TextField(blank=True, default='')

    class Meta(BaseModel.Meta):
        db_table='patient'


class PatientDoctorMapping(BaseModel):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='doctor_mappings',
        limit_choices_to={'is_deleted': False}
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='patient_mappings',
        limit_choices_to={'is_deleted': False}
    )

    class Meta(BaseModel.Meta):
        db_table = 'patient_doctor_mapping'
        constraints = [
            models.UniqueConstraint(
                fields=['patient', 'doctor'],
                condition=models.Q(is_deleted=False),
                name='unique_active_mapping'
            )
        ]
