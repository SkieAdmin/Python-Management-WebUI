from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import (
    Attendance, Leave, Payroll, Department, Employee, User, Holiday, PayRate,
    EmployeeDepartment, Deductions, Position
)
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from calendar import monthrange
import calendar
import pytz
from collections import defaultdict
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
from .forms import HolidayForm

def landing_page(request):
    return render(request, 'attendance/landing_page.html')

def redirect_from_admin(request):
    return redirect('admin_dashboard')

# Check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_admin


def admin_dashboard(request):
    employees = Employee.objects.all()
    departments = Department.objects.all()
    positions = Position.objects.all()
    context = {
        'employees': employees,
        'departments': departments,
        'positions': positions,
    }
    return render(request, 'attendance/admin_dashboard.html', context)

# Registration View
def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        department_id = request.POST['department']
        position_id = request.POST['position']
        age = request.POST['age']

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect('register')

        if not Department.objects.filter(id=department_id).exists():
            messages.error(request, "Invalid department selected.")
            return redirect('register')

        department = get_object_or_404(Department, id=department_id)
        position = get_object_or_404(Position, id=position_id)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_admin=False
        )

        employee = Employee.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            age=age,
            position=position
        )

        EmployeeDepartment.objects.create(
            employee=employee,
            department=department
        )

        messages.success(request, "Account created successfully!")
        return redirect('login')

    departments = Department.objects.all()
    positions = Position.objects.all()

    if not departments:
        messages.warning(request, "No departments available. Please add some departments.")

    return render(request, 'attendance/register.html', {
        'departments': departments,
        'positions': positions
    })

# Login View
def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_admin:
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'attendance/login.html')

# Logout View
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')

# Dashboard View
@login_required
def dashboard(request):
    employee = getattr(request.user, 'employee', None)
    context = {
        'is_admin': request.user.is_admin,
        'employee': employee,
    }
    return render(request, 'attendance/dashboard.html', context)

# Record Attendance View
@login_required
def record_attendance(request):
    employee = get_object_or_404(Employee, user=request.user)
    today = timezone.now().date()
    holiday = Holiday.objects.filter(date=today).first()
    holidays = Holiday.objects.all().order_by('date')
    holiday_map = {h.date: h for h in holidays}

    user_timezone = pytz.timezone('Asia/Manila')
    current_time = timezone.now().astimezone(user_timezone).time()

    attendance, created = Attendance.objects.get_or_create(employee=employee, date=today)

    if not holiday and request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'time_in' and not attendance.time_in:
            attendance.time_in = current_time
            attendance.save()
            messages.success(request, "Time In recorded!")

        elif action == 'time_out' and attendance.time_in and not attendance.time_out:
            attendance.time_out = current_time
            start = datetime.combine(attendance.date, attendance.time_in)
            end = datetime.combine(attendance.date, attendance.time_out)
            duration = end - start
            attendance.total_hours = round(duration.total_seconds() / 3600, 2)
            attendance.save()
            messages.success(request, "Time Out recorded!")

    if attendance.time_in and attendance.time_out and attendance.total_hours is None:
        start = datetime.combine(attendance.date, attendance.time_in)
        end = datetime.combine(attendance.date, attendance.time_out)
        duration = end - start
        attendance.total_hours = round(duration.total_seconds() / 3600, 2)
        attendance.save()

    dtr_records = Attendance.objects.filter(employee=employee).order_by('-date')

    for rec in dtr_records:
        holiday_obj = holiday_map.get(rec.date)
        rec.holiday_name = holiday_obj.description if holiday_obj else None

    return render(request, 'attendance/attendance.html', {
        'attendance': attendance,
        'dtr_records': dtr_records,
        'holiday': holiday,
        'holidays': holidays,
        'holiday_map': holiday_map,
    })

# Submit Leave Request
@login_required
def submit_leave_request(request):
    employee = get_object_or_404(Employee, user=request.user)

    if request.method == 'POST':
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        reason = request.POST['reason']

        now = timezone.now()
        current_month = now.month
        current_year = now.year

        monthly_leave_count = Leave.objects.filter(
            employee=employee,
            start_date__month=current_month,
            start_date__year=current_year
        ).count()

        MAX_LEAVES_PER_MONTH = 3

        if monthly_leave_count >= MAX_LEAVES_PER_MONTH:
            messages.error(request, f"You have already submitted {MAX_LEAVES_PER_MONTH} leave requests this month.")
            return redirect('leave_request')

        Leave.objects.create(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status='Pending'
        )
        messages.success(request, "Leave request submitted!")
        return redirect('leave_request')

    leave_requests = Leave.objects.filter(employee=employee).order_by('-start_date')

    return render(request, 'attendance/leave_request.html', {
        'leave_requests': leave_requests
    })

# View Leave Requests with Pagination
@login_required
def leave_list(request):
    if request.user.is_admin:
        leaves = Leave.objects.all()
    else:
        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            messages.error(request, "Employee record not found for this user.")
            return redirect('dashboard')

        leaves = Leave.objects.filter(employee=employee)

    paginator = Paginator(leaves, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'attendance/leave_list.html', {'page_obj': page_obj})

# Generate Payroll
from datetime import datetime

@user_passes_test(is_admin)
def generate_payroll(request):
    if request.method == 'POST':
        month = int(request.POST['month'])
        year = int(request.POST['year'])

        employees = Employee.objects.all()

        for employee in employees:
            attendances = Attendance.objects.filter(
                employee=employee,
                date__year=year,
                date__month=month
            )
            total_hours = sum(a.total_hours or 0 for a in attendances)

            payrate_obj = PayRate.objects.filter(employee=employee).first()
            pay_rate = payrate_obj.pay_rate if payrate_obj else 0

            gross_salary = total_hours * pay_rate

            payroll, _ = Payroll.objects.update_or_create(
                employee=employee,
                pay_period=datetime(year, month, 1),
                defaults={
                    'gross_salary': gross_salary,
                    'net_salary': gross_salary
                }
            )

            deductions = Deductions.objects.filter(payroll=payroll)
            total_deductions = sum(d.salary_deduction for d in deductions)

            payroll.total_deductions = total_deductions
            payroll.net_salary = gross_salary - total_deductions
            payroll.save()

        messages.success(request, "Payroll generated successfully!")
        return redirect('admin_dashboard')

    return render(request, 'attendance/generate_payroll.html', {
        'months': range(1, 13),
        'current_year': datetime.now().year
    })

# View Payroll Summary
@login_required
def view_payroll(request):
    employee = get_object_or_404(Employee, user=request.user)
    payrolls = Payroll.objects.filter(employee=employee)
    return render(request, 'attendance/payroll.html', {
        'employee': employee,
        'payrolls': payrolls,
    })

# View PayRate (was Pass)
@login_required
def view_payrate(request):
    employee = get_object_or_404(Employee, user=request.user)
    payrates = PayRate.objects.filter(employee=employee)
    return render(request, 'attendance/payrate.html', {'payrates': payrates})

# Holiday list
@user_passes_test(is_admin)
def holiday_list(request):
    holidays = Holiday.objects.all().order_by('date')
    return render(request, 'attendance/holiday_list.html', {'holidays': holidays})

# Create holiday view
@user_passes_test(is_admin)
def add_holiday(request):
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('holiday_list') 
    else:
        form = HolidayForm()
    return render(request, 'attendance/add_holiday.html', {'form': form})

# Update holiday view
@user_passes_test(is_admin)
def update_holiday(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=holiday)
        if form.is_valid():
            form.save()
            return redirect('holiday_list')  
    else:
        form = HolidayForm(instance=holiday)
    return render(request, 'attendance/update_holiday.html', {'form': form})

# Delete holiday view
@user_passes_test(is_admin)
def delete_holiday(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)
    if request.method == 'POST':
        holiday.delete()
        return redirect('holiday_list')  
    return render(request, 'attendance/delete_holiday.html', {'holiday': holiday})

# Admin Approve Leave
@user_passes_test(is_admin)
def approve_leave(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    leave.status = 'Approved'
    leave.admin = request.user
    leave.save()
    messages.success(request, "Leave approved.")
    return redirect('leave_list')

# Admin Reject Leave
@user_passes_test(is_admin)
def reject_leave(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    leave.status = 'Rejected'
    leave.admin = request.user
    leave.save()
    messages.warning(request, "Leave rejected.")
    return redirect('leave_list')

# --- DEPARTMENT MANAGEMENT ---

# Department List View with Pagination
@user_passes_test(is_admin)
def department_list(request):
    departments = Department.objects.all()
    paginator = Paginator(departments, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'attendance/department_list.html', {'page_obj': page_obj})

# Add Department View with validation
@user_passes_test(is_admin)
def add_department(request):
    if request.method == 'POST':
        dept_name = request.POST.get('department_name') 
        if dept_name:
            Department.objects.create(department_name=dept_name)
            return redirect('department_list')
    return render(request, 'attendance/add_department.html')

@user_passes_test(is_admin)
def edit_department(request, department_id):
    try:
        department = Department.objects.get(id=department_id)
    except Department.DoesNotExist:
        messages.error(request, "Department not found.")
        return redirect('department_list')

    if request.method == 'POST':
        department.department_name = request.POST['department_name']
        department.save()
        messages.success(request, 'Department updated successfully.')
        return redirect('department_list')
    
    return render(request, 'attendance/edit_department.html', {'department': department})

@user_passes_test(is_admin)
def delete_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    department.delete()
    return redirect('department_list')


# --- POSITION MANAGEMENT ---

# Position List View with Pagination
@user_passes_test(is_admin)
def position_list(request):
    positions = Position.objects.all()
    paginator = Paginator(positions, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'attendance/position_list.html', {'page_obj': page_obj})

# Add Position View with validation
@user_passes_test(is_admin)
def add_position(request):
    if request.method == 'POST':
        name = request.POST['position_name']
        if Position.objects.filter(name=name).exists():
            messages.error(request, "Position with this name already exists.")
            return redirect('add_position')

        Position.objects.create(name=name)
        messages.success(request, 'Position added successfully.')
        return redirect('position_list')
    return render(request, 'attendance/add_position.html')

@user_passes_test(is_admin)
def update_position(request, position_id):
    position = get_object_or_404(Position, id=position_id)
    if request.method == 'POST':
        position.name = request.POST['position_name']
        position.save()
        messages.success(request, 'Position updated successfully.')
        return redirect('position_list')
    return render(request, 'attendance/edit_position.html', {'position': position})

@user_passes_test(is_admin)
def delete_position(request, position_id):
    position = get_object_or_404(Position, id=position_id)
    position.delete()
    messages.success(request, 'Position deleted successfully.')
    return redirect('position_list')

def employee_detail(request, id):
    employee = get_object_or_404(Employee, id=id)
    return render(request, 'attendance/employee_detail.html', {'employee': employee})

@user_passes_test(is_admin)
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'attendance/employee_list.html', {'employees': employees})