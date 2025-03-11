import pytest
from core.models import User, DoctorProfile, PatientProfile, Clinic


@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user(
        username="doctor1",
        password="testpass",
        role="doctor")
    doctor_profile = DoctorProfile.objects.create(
        user=user, specialization="Кардиолог")
    clinic = Clinic.objects.create(
        name="Test Clinic",
        legal_address="Адрес 1",
        physical_address="Адрес 2")
    doctor_profile.clinics.add(clinic)
    print(f"Создан доктор: {user.username}, профиль: {doctor_profile}")
    return user


@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(
        username="patient1",
        password="testpass",
        role="patient")
    PatientProfile.objects.create(
        user=user,
        phone="Не указан",
        email="test@example.com")
    return user


@pytest.fixture
def clinic(db):
    return Clinic.objects.create(
        name="Test Clinic",
        legal_address="Адрес 1",
        physical_address="Адрес 2")
