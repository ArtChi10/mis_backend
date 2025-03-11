import pytest
from django.contrib.auth import get_user_model
from core.models import Consultation, Clinic, DoctorProfile
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.test import APIClient


User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", password="adminpass", role="admin")


@pytest.fixture
def clinic(db):
    return Clinic.objects.create(
        name="Test Clinic",
        legal_address="123 Legal St",
        physical_address="456 Physical St")


@pytest.fixture
def doctor_user(db, clinic):
    doctor = User.objects.create_user(
        username="doctor1",
        password="doctorpass",
        role="doctor")
    doctor_profile = DoctorProfile.objects.create(
        user=doctor, specialization="Терапевт")
    doctor_profile.clinics.add(clinic)
    return doctor


@pytest.fixture
def patient_user(db):
    return User.objects.create_user(
        username="patient1",
        password="patientpass",
        role="patient")


@pytest.mark.django_db
def test_create_consultation(patient_user, doctor_user, clinic):
    client = APIClient()
    client.force_authenticate(user=patient_user)

    response = client.post("/api/consultations/", {
        "doctor": doctor_user.id,
        "clinic": clinic.id,
        "start_time": "2025-04-10T10:00:00Z"
    }, format="json")

    assert response.status_code == 201
    assert Consultation.objects.count() == 1


@pytest.mark.django_db
def test_list_consultations(patient_user, doctor_user, clinic):
    client = APIClient()
    client.force_authenticate(user=patient_user)

    Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time="2025-04-10T10:00:00Z",
        end_time="2025-04-10T11:00:00Z",
        status="ожидает"
    )

    response = client.get("/api/consultations/")
    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_list_consultations_with_filters(
        admin_user, doctor_user, patient_user, clinic):
    client = APIClient()
    # ✅ Администратор видит все консультации
    client.force_authenticate(user=admin_user)

    Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time="2025-04-10T10:00:00Z",
        end_time="2025-04-10T11:00:00Z",
        status="ожидает")
    Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time="2025-04-11T10:00:00Z",
        end_time="2025-04-11T11:00:00Z",
        status="подтверждена")
    Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time="2025-04-12T10:00:00Z",
        end_time="2025-04-12T11:00:00Z",
        status="завершена")

    response = client.get("/api/consultations/", {"status": "ожидает"})

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_admin_sets_schedule(admin_user, doctor_user, patient_user, clinic):
    client = APIClient()
    client.force_authenticate(user=admin_user)

    consultation = Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time="2025-04-10T10:00:00Z",
        end_time="2025-04-10T11:00:00Z",
        status="ожидает"
    )

    new_start_time = "2025-04-15T14:00:00Z"
    response = client.patch(
        f"/api/consultations/{consultation.id}/set_schedule/",
        {"start_time": new_start_time})

    assert response.status_code == 200
    consultation.refresh_from_db()
    assert consultation.start_time.strftime(
        "%Y-%m-%dT%H:%M:%SZ") == new_start_time
    assert consultation.status == "подтверждена"


@pytest.mark.django_db
def test_auto_update_status(admin_user, doctor_user, patient_user, clinic):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    past_start_time = now() - timedelta(hours=2)
    past_end_time = now() - timedelta(hours=1)

    consultation = Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time=past_start_time,
        end_time=past_end_time,
        status="подтверждена"
    )
    response = client.patch("/api/consultations/update_status/")
    assert response.status_code == 200
    consultation.refresh_from_db()
    assert consultation.status == "завершена"


@pytest.mark.django_db
def test_admin_can_delete_consultation_before_start(
        admin_user, doctor_user, patient_user, clinic):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    future_start_time = now() + timedelta(days=1)  # Консультация завтра
    future_end_time = future_start_time + timedelta(hours=1)
    consultation = Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time=future_start_time,
        end_time=future_end_time,
        status="подтверждена"
    )
    response = client.delete(f"/api/consultations/{consultation.id}/")
    assert response.status_code == 204  # ✅ Удалено
    assert Consultation.objects.filter(
        id=consultation.id).count() == 0  # ✅ В базе больше нет


@pytest.mark.django_db
def test_admin_cannot_delete_started_consultation(
        admin_user, doctor_user, patient_user, clinic):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    past_start_time = now() - timedelta(hours=2)
    past_end_time = past_start_time + timedelta(hours=1)
    consultation = Consultation.objects.create(
        doctor=doctor_user,
        patient=patient_user,
        clinic=clinic,
        start_time=past_start_time,
        end_time=past_end_time,
        status="начата"
    )

    response = client.delete(f"/api/consultations/{consultation.id}/")
    assert response.status_code == 403
    assert Consultation.objects.filter(id=consultation.id).count() == 1


@pytest.mark.django_db
def test_get_specializations(admin_user, doctor_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    DoctorProfile.objects.get_or_create(
        user=doctor_user, defaults={
            "specialization": "Терапевт"})
    another_doctor = User.objects.create_user(
        username="doctor2", password="doctorpass", role="doctor")
    DoctorProfile.objects.get_or_create(
        user=another_doctor, defaults={
            "specialization": "Хирург"})
    response = client.get("/api/consultations/specializations/")
    assert response.status_code == 200
    assert "Терапевт" in response.data["specializations"]
    assert "Хирург" in response.data["specializations"]


@pytest.mark.django_db
def test_get_clinics_by_specialization(admin_user, doctor_user, clinic):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    doctor_profile, _ = DoctorProfile.objects.get_or_create(
        user=doctor_user, defaults={"specialization": "Терапевт"})
    doctor_profile.clinics.add(clinic)
    response = client.get(
        "/api/consultations/clinics_by_specialization/?specialization=Терапевт")
    assert response.status_code == 200
    assert len(response.data["clinics"]) == 1
    assert response.data["clinics"][0]["name"] == clinic.name


@pytest.mark.django_db
def test_get_doctors_by_clinic(admin_user, doctor_user, clinic):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    doctor_profile, _ = DoctorProfile.objects.get_or_create(
        user=doctor_user, defaults={"specialization": "Терапевт"})
    doctor_profile.clinics.add(clinic)
    response = client.get(
        f"/api/consultations/doctors_by_clinic/?specialization=Терапевт&clinic={clinic.id}")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == doctor_user.id
    assert response.data[0]["name"] == f"{doctor_user.last_name} {doctor_user.first_name}"


@pytest.mark.django_db
def test_get_available_dates(admin_user, doctor_user, clinic):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    doctor_profile, _ = DoctorProfile.objects.get_or_create(
        user=doctor_user, defaults={"specialization": "Терапевт"})
    doctor_profile.clinics.add(clinic)
    response = client.get(
        f"/api/consultations/available_dates/?doctor={doctor_user.id}")
    assert response.status_code == 200
    assert "available_dates" in response.data
    assert len(response.data["available_dates"]) <= 3


@pytest.mark.django_db
def test_patient_cannot_create_consultation_with_unlinked_doctor(
        patient_user, doctor_user):
    client = APIClient()
    client.force_authenticate(user=patient_user)
    another_clinic = Clinic.objects.create(
        name="Other Clinic",
        legal_address="789 Another St",
        physical_address="890 Another St")
    response = client.post("/api/consultations/", {
        "doctor": doctor_user.id,
        "clinic": another_clinic.id,
        "start_time": "2025-04-10T10:00:00Z"
    }, format="json")

    assert response.status_code == 400
    assert "Этот врач не работает в выбранной клинике." in str(response.data)


@pytest.mark.django_db
def test_patient_cannot_create_past_consultation(
        patient_user, doctor_user, clinic):
    client = APIClient()
    client.force_authenticate(user=patient_user)
    past_time = (now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    response = client.post("/api/consultations/", {
        "doctor": doctor_user.id,
        "clinic": clinic.id,
        "start_time": past_time
    }, format="json")
    assert response.status_code == 400
    assert "Нельзя записаться на консультацию в прошлом" in response.data[0]
