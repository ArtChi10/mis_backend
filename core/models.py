from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='patient')
    middle_name = models.CharField(
        max_length=150,
        blank=True,
        null=True)  # ✅ Отчество

    def __str__(self):
        return f"{self.username} ({self.last_name} {self.first_name} {self.middle_name}, {self.role})"


class Clinic(models.Model):
    name = models.CharField(max_length=255)
    legal_address = models.TextField()
    physical_address = models.TextField()

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile")
    specialization = models.CharField(max_length=255)
    clinics = models.ManyToManyField(Clinic, related_name="doctors")

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name} ({self.specialization})"


class PatientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile")
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name} ({self.phone})"


class Consultation(models.Model):
    STATUS_CHOICES = [
        ('подтверждена', 'Подтверждена'),
        ('ожидает', 'Ожидает'),
        ('начата', 'Начата'),
        ('завершена', 'Завершена'),
        ('оплачена', 'Оплачена'),
    ]

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consultations_as_doctor")
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consultations_as_patient")
    clinic = models.ForeignKey(
        'Clinic',
        on_delete=models.CASCADE,
        related_name="consultations")
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ожидает')
    notes = models.TextField(blank=True, null=True)

    def clean(self):
        overlapping_consultations = Consultation.objects.filter(
            doctor=self.doctor,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id)

        if overlapping_consultations.exists():
            raise ValidationError(
                "Доктор уже записан на другую консультацию в это время!")

        clinic_conflicts = overlapping_consultations.exclude(
            clinic=self.clinic)
        if clinic_conflicts.exists():
            raise ValidationError(
                "Доктор не может работать в двух клиниках одновременно!")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Консультация {self.doctor.username} с {self.patient.username} ({self.status}) в {self.clinic.name}"
