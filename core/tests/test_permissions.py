import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Consultation, Clinic

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", password="adminpass", role="admin")


@pytest.fixture
def doctor_user(db):
    return User.objects.create_user(
        username="doctor1",
        password="doctorpass",
        role="doctor")


@pytest.fixture
def patient_user(db):
    return User.objects.create_user(
        username="patient1",
        password="patientpass",
        role="patient")


@pytest.fixture
def clinic(db):
    return Clinic.objects.create(
        name="Test Clinic",
        legal_address="123 Legal St",
        physical_address="456 Physical St")


@pytest.fixture
def consultation(db, doctor_user, patient_user, clinic):
    return Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time="2025-04-10T10:00:00Z",
        end_time="2025-04-10T11:00:00Z"
    )


@pytest.mark.django_db
def test_patient_cannot_delete_consultation(patient_user, consultation):
    client = APIClient()
    client.force_authenticate(user=patient_user)
    response = client.delete(f"/api/consultations/{consultation.id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_doctor_cannot_delete_consultation(doctor_user, consultation):
    client = APIClient()
    client.force_authenticate(user=doctor_user)
    response = client.delete(f"/api/consultations/{consultation.id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_delete_consultation(admin_user, consultation):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    response = client.delete(f"/api/consultations/{consultation.id}/")
    assert response.status_code == 204
    assert Consultation.objects.count() == 0


@pytest.mark.django_db
def test_only_admin_can_set_paid_status(
        doctor_user,
        patient_user,
        admin_user,
        consultation):
    client_doctor = APIClient()
    client_doctor.force_authenticate(user=doctor_user)
    response = client_doctor.patch(
        f"/api/consultations/{consultation.id}/set_paid_status/")
    assert response.status_code == 403
    client_patient = APIClient()
    client_patient.force_authenticate(user=patient_user)
    response = client_patient.patch(
        f"/api/consultations/{consultation.id}/set_paid_status/")
    assert response.status_code == 403
    client_admin = APIClient()
    client_admin.force_authenticate(user=admin_user)
    consultation.status = "завершена"
    consultation.save()

    response = client_admin.patch(
        f"/api/consultations/{consultation.id}/set_paid_status/")
    assert response.status_code == 200
    assert Consultation.objects.get(id=consultation.id).status == "оплачена"
