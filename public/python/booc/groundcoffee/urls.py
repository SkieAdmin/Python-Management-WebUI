from django.contrib import admin
from django.urls    import path, include
from django.conf    import settings
from django.conf.urls.static import static

urlpatterns = [
    # Default Django admin (optional)
    path('admin/', admin.site.urls),

    # Your public-facing shop
    path('', include('shop.urls')),

    # Custom admin panel under /adminpanel/
    path('adminpanel/', include('shop.adminpanel.urls', namespace='shop_admin')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
