from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (UserSerializer,
                          CustomTokenObtainSerializer, ConsultationSerializer)
from .models import Consultation, PatientProfile
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .permissions import IsPatientOrAdmin
from rest_framework.decorators import action
from datetime import timedelta
from django.utils.timezone import now
from .models import DoctorProfile, Clinic, User
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_datetime


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        if user.role == "doctor":
            DoctorProfile.objects.create(
                user=user, specialization="Не указано")

        elif user.role == "patient":
            PatientProfile.objects.create(
                user=user, phone="Не указан", email=user.email)


class CustomTokenObtainView(TokenObtainPairView):
    serializer_class = CustomTokenObtainSerializer


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {"message": "Ты получил доступ к защищенному эндпоинту!",
             "user": request.user.username})


class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsPatientOrAdmin]
    queryset = Consultation.objects.all()
    filterset_fields = ['status', 'clinic', 'doctor', 'patient']
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def destroy(self, request, *args, **kwargs):
        consultation = self.get_object()
        if request.user.role != "admin":
            return Response(
                {"error": "Только администратор удаляет консультации."},
                status=403)
        if consultation.start_time <= now():
            return Response(
                {"error": "Нельзя удалить консультацию, которая началась."},
                status=403)
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != "patient":
            raise ValidationError(
                "Только пациенты могут создавать заявки на консультацию.")
        data = serializer.validated_data
        doctor = data.get("doctor")
        clinic = data.get("clinic")
        start_time = data.get("start_time")
        if not doctor or not clinic or not start_time:
            raise ValidationError(
                "Нужно указать врача, клинику и желаемую дату.")
        if start_time < now():
            raise ValidationError(
                "Нельзя записаться на консультацию в прошлом.")
        if not doctor.doctor_profile.clinics.filter(id=clinic.id).exists():
            raise ValidationError("Этот врач не работает в выбранной клинике.")
        end_time = start_time + timedelta(hours=1)
        serializer.save(
            patient=user,
            end_time=end_time,
            status="ожидает",
            clinic=clinic,
            doctor=doctor)

    @action(detail=False, methods=["get"])
    def specializations(self, request):
        specializations = DoctorProfile.objects.values_list(
            "specialization", flat=True).distinct()
        return Response({"specializations": list(specializations)})

    @action(detail=True, methods=["patch"])
    def set_schedule(self, request, pk=None):
        consultation = self.get_object()
        if request.user.role != "admin":
            return Response(
                {"error": "Администратор может назначить время консультации."},
                status=403)
        if "start_time" not in request.data:
            return Response(
                {"error": "Требуется указать точное время начала."},
                status=400)
        start_time = parse_datetime(request.data["start_time"])
        if not start_time:
            return Response(
                {"error": "Неверный формат даты. Используйте ISO 8601."},
                status=400)
        end_time = start_time + timedelta(hours=1)

        overlapping_consultations = Consultation.objects.filter(
            doctor=consultation.doctor,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()
        if overlapping_consultations:
            return Response(
                {"error": "Этот врач уже занят в это время!"}, status=400)

        clinic_conflict = Consultation.objects.filter(
            doctor=consultation.doctor,
            start_time__date=start_time.date()
        ).exclude(clinic=consultation.clinic).exists()
        if clinic_conflict:
            return Response(
                {
                    "error": "Врач нельзя работать в разных клиниках в 1 день."
                },
                status=400)
        consultation.start_time = start_time
        consultation.end_time = end_time
        consultation.status = "подтверждена"
        consultation.save()
        return Response(
            {"message": "Время консультации назначено, статус обновлён."},
            status=200)

    @action(detail=False, methods=["patch"])
    def update_status(self, request):
        now_time = now()
        Consultation.objects.filter(
            status="подтверждена",
            start_time__lte=now_time).update(
            status="начата")
        Consultation.objects.filter(
            status="начата",
            end_time__lte=now_time).update(
            status="завершена")
        return Response({"message": "Статусы обновлены."}, status=200)

    @action(detail=False, methods=["get"])
    def clinics_by_specialization(self, request):
        specialization = request.query_params.get("specialization", None)
        if not specialization:
            return Response({"error": "Укажите специальность."}, status=400)
        clinics = Clinic.objects.filter(
            doctors__specialization=specialization).distinct()
        return Response(
            {
                "clinics": [
                    {
                        "id": clinic.id,
                        "name": clinic.name
                    }
                    for clinic in clinics]
            })

    @action(detail=False, methods=["get"])
    def doctors_by_clinic(self, request):
        specialization = request.query_params.get("specialization", None)
        clinic_id = request.query_params.get("clinic", None)
        if not specialization or not clinic_id:
            return Response({"error": "Укажите специальность и ID клиники."},
                            status=400)
        doctors = DoctorProfile.objects.filter(
            specialization=specialization, clinics__id=clinic_id
        ).select_related("user")
        return Response([
            {
                "id": doctor.user.id,
                "name": f"{doctor.user.last_name} {doctor.user.first_name}"}
            for doctor in doctors
        ])

    @action(detail=False, methods=["get"])
    def available_dates(self, request):
        doctor_id = request.query_params.get("doctor", None)
        if not doctor_id:
            return Response({"error": "Укажите ID врача."}, status=400)
        doctor = User.objects.get(id=doctor_id)
        available_dates = []
        today = now().date()
        for i in range(1, 14):
            check_date = today + timedelta(days=i)
            busy_slots = Consultation.objects.filter(
                doctor=doctor,
                start_time__date=check_date
            ).count()
            if busy_slots < 8:
                available_dates.append(str(check_date))
            if len(available_dates) >= 3:
                break
        return Response({"available_dates": available_dates})

    @action(detail=True, methods=["patch"])
    def set_paid_status(self, request, pk=None):
        consultation = self.get_object()
        if request.user.role != "admin":
            return Response(
                {"error": "Только админ может изменять статус оплаты."},
                status=403
            )
        if consultation.status != "завершена":
            return Response(
                {
                    "error": "Потверждение оплаты только для завершенных."},
                status=400
            )
        consultation.status = "оплачена"
        consultation.save()
        return Response({"message": "Статус консультации обновлён: оплачена."})
