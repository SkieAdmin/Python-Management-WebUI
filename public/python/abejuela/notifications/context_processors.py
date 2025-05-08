def notifications(request):
    notifications_list = []
    if request.user.is_authenticated:
        from notifications.models import Notification
        notifications_list = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).order_by('-created_at')
    
    return {
        'notifications': notifications_list,
        'notification_count': len(notifications_list),
    }
