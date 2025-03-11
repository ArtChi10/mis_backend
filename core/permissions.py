from rest_framework.permissions import BasePermission
from rest_framework import permissions


class IsDoctorOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.method in ['GET'] or request.user.role == 'doctor')


class IsOwnerOrAdmin(BasePermission):

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role == "admin":
            return True
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return request.user == obj.doctor or request.user == obj.patient


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == "admin"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == "admin"


class IsPatientOrAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == "POST":
            return (request.user.is_authenticated and request.user.role == "patient")
        elif request.method in ["DELETE", "PUT", "PATCH"]:
            return (request.user.is_authenticated and request.user.role == "admin")
        return request.user.is_authenticated
