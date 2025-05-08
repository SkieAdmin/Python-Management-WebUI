from django.http import HttpResponseForbidden
from .models import Employee

def role_required(role):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            try:
                employee = Employee.objects.get(user=request.user)
                if employee.role == role:
                    return view_func(request, *args, **kwargs)
            except Employee.DoesNotExist:
                pass
            return HttpResponseForbidden("403 Forbidden: You don’t have permission to access this page.")
        return _wrapped_view
    return decorator
