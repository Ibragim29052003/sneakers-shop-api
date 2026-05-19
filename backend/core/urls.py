"""
Конфигурация URL для основного проекта.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import DebugSentryView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('users.urls')),
    path('api/v1/auth/', include('dj_rest_auth.urls')),
    path('api/v1/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/v1/auth/google/', include('users.social_urls')),
    path('api/v1/', include('products.urls')),
    path('api/v1/', include('orders.urls')),
    path('api/v1/', include('reviews.urls')),
    path('api/v1/', include('carts.urls')),
    path('api/v1/', include('suppliers.urls')),
    path('api/v1/debug/sentry/', DebugSentryView.as_view(), name='debug-sentry'),
]

if settings.ENABLE_SILK:
    urlpatterns += [
        path('silk/', include('silk.urls', namespace='silk')),
    ]

# Обслуживание медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns = [
        path('__debug__/', include('debug_toolbar.urls')),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
