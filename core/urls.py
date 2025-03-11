from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (RegisterView,
                    CustomTokenObtainView, ConsultationViewSet, ProtectedView)


router = DefaultRouter()
router.register(
    r'consultations',
    ConsultationViewSet,
    basename='consultations')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('protected/', ProtectedView.as_view(), name='protected'),
    path('', include(router.urls)),
]
