from django.db import models
from django.contrib.auth.models import User


class Report(models.Model):
    REPORT_TYPES = (
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('payment', 'Payment Report'),
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    generated_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.title}"
