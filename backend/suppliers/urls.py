"""
Конфигурация URL для приложения поставщиков
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Справочники
    ContractStatusViewSet,
    RequestStatusViewSet,
    DocumentTypeViewSet,
    AlertTypeViewSet,
    ProductSupplierSourceViewSet,
    # Основные представления
    SupplierViewSet,
    SupplierContractViewSet,
    ContractDocumentViewSet,
    SupplierProductRequestViewSet,
    RequestDocumentViewSet,
    SupplierProductViewSet,
    SystemAlertViewSet,
    # Пользовательские представления
    AssignManagerView,
    UserAlertsView,
    CreateProductFromRequestView,
)

router = DefaultRouter()

# Справочники (только админ)
router.register(r'contract-statuses', ContractStatusViewSet, basename='contract-status')
router.register(r'request-statuses', RequestStatusViewSet, basename='request-status')
router.register(r'document-types', DocumentTypeViewSet, basename='document-type')
router.register(r'alert-types', AlertTypeViewSet, basename='alert-type')
router.register(r'product-sources', ProductSupplierSourceViewSet, basename='product-source')

# Основные ресурсы
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'supplier-contracts', SupplierContractViewSet, basename='supplier-contract')
router.register(r'contract-documents', ContractDocumentViewSet, basename='contract-document')
router.register(r'supplier-requests', SupplierProductRequestViewSet, basename='supplier-request')
router.register(r'request-documents', RequestDocumentViewSet, basename='request-document')
router.register(r'supplier-products', SupplierProductViewSet, basename='supplier-product')
router.register(r'system-alerts', SystemAlertViewSet, basename='system-alert')

urlpatterns = [
    path('', include(router.urls)),
    
    # Пользовательские эндпоинты
    path('supplier-requests/<int:request_id>/assign-manager/', 
         AssignManagerView.as_view(), 
         name='assign-manager'),
    path('supplier-requests/<int:request_id>/create-product/', 
         CreateProductFromRequestView.as_view(), 
         name='create-product-from-request'),
    path('my-alerts/', 
         UserAlertsView.as_view(), 
         name='user-alerts'),
]
