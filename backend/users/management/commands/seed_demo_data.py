from __future__ import annotations

import base64
import mimetypes
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from carts.models import Cart, CartItem
from orders.models import Order, OrderItem, OrderStatus
from products.models import (
    Category,
    FilterGroup,
    FilterOption,
    Product,
    ProductFavorite,
    ProductFilter,
    ProductImage,
    SliderImage,
)
from reviews.models import Review
from suppliers.models import (
    AlertType,
    ContractDocument,
    ContractStatus,
    DocumentType,
    ProductSupplierSource,
    RequestCommunication,
    RequestDocument,
    RequestStatus,
    Supplier,
    SupplierContract,
    SupplierProduct,
    SupplierProductRequest,
    SystemAlert,
)
from users.models import Role, UserProfile, UserRole


TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO0qf6sAAAAASUVORK5CYII="
)

SNEAKER_IMAGE_URLS = [
    f"https://loremflickr.com/1200/900/{topic}?lock={100 + idx}"
    for idx, topic in enumerate(
        [
            "sneaker",
            "running-shoes",
            "sneaker,shoe",
            "trainers",
            "athletic-shoes",
            "sports-shoes",
            "sneakers,streetwear",
            "shoe,footwear",
        ]
        * 15,
        start=1,
    )
]

SLIDER_SEED_ASSETS_DIR = Path(__file__).resolve().parent / "seed_assets" / "slider"
SLIDER_SEED_FILENAMES = [
    "slide_01.png",
    "slide_02.png",
    "slide_03.png",
    "slide_04.png",
    "slide_05.png",
    "slide_06.png",
    "slide_07.png",
    "slide_08.png",
]


class Command(BaseCommand):
    help = "Fill database with demo data for API testing and Postman demo."

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """Точка входа команды: заполняет БД связанным демо-набором данных."""
        user_model = get_user_model()

        roles = self._seed_roles()
        users = self._seed_users(user_model, roles)
        supplier_context = self._seed_suppliers(users)
        product_context = self._seed_products(supplier_context)
        self._seed_cart_and_orders(users, product_context)
        self._seed_reviews(users, product_context)
        self._seed_favorites(users, product_context)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    def _seed_roles(self) -> dict[str, Role]:
        """Создает или обновляет системные роли пользователей."""
        roles: dict[str, Role] = {}
        for name, description in [
            ("user", "Customer role"),
            ("admin", "Administrator role"),
            ("manager", "Manager role"),
            ("supplier", "Supplier role"),
        ]:
            role, _ = Role.objects.get_or_create(name=name, defaults={"description": description})
            if role.description != description:
                role.description = description
                role.save(update_fields=["description"])
            roles[name] = role
        return roles

    def _upsert_user(
        self,
        user_model: Any,
        email: str,
        password: str,
        *,
        first_name: str,
        last_name: str,
        is_staff: bool = False,
        is_superuser: bool = False,
        role: Role,
    ) -> Any:
        """Создает или обновляет пользователя, его профиль и роль."""
        user, created = user_model.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_active": True,
            },
        )
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.is_active = True
        user.set_password(password)
        user.save()

        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "phone": "+79000000000",
                "address": "Demo street, 10",
                "city": "Moscow",
                "postal_code": "101000",
                "country": "Russia",
            },
        )
        UserRole.objects.get_or_create(user=user, role=role)

        action = "created" if created else "updated"
        self.stdout.write(f"  user {email}: {action}")
        return user

    def _seed_users(self, user_model: Any, roles: dict[str, Role]) -> dict[str, Any]:
        """Формирует демо-пользователей для ролей admin, manager, buyer и supplier."""
        users: dict[str, Any] = {}

        users["admin"] = self._upsert_user(
            user_model,
            "admin@test.com",
            "testpass123",
            first_name="Admin",
            last_name="User",
            is_staff=True,
            is_superuser=True,
            role=roles["admin"],
        )
        users["manager"] = self._upsert_user(
            user_model,
            "manager@test.com",
            "testpass123",
            first_name="Manager",
            last_name="User",
            is_staff=False,
            is_superuser=False,
            role=roles["manager"],
        )
        users["buyer"] = self._upsert_user(
            user_model,
            "buyer@test.com",
            "testpass123",
            first_name="Buyer",
            last_name="One",
            role=roles["user"],
        )
        users["buyer_new"] = self._upsert_user(
            user_model,
            "buyer_new@test.com",
            "testpass123",
            first_name="Buyer",
            last_name="New",
            role=roles["user"],
        )
        users["other"] = self._upsert_user(
            user_model,
            "other@test.com",
            "testpass123",
            first_name="Other",
            last_name="Buyer",
            role=roles["user"],
        )
        users["supplier_user"] = self._upsert_user(
            user_model,
            "supplier@test.com",
            "testpass123",
            first_name="Supplier",
            last_name="User",
            role=roles["supplier"],
        )

        return users

    def _seed_suppliers(self, users: dict[str, Any]) -> dict[str, Any]:
        """Заполняет справочники поставщиков и создает демо-контракт с заявкой."""
        for status_name, description in [
            (ContractStatus.DRAFT, "Draft"),
            (ContractStatus.ACTIVE, "Active"),
            (ContractStatus.SUSPENDED, "Suspended"),
            (ContractStatus.EXPIRED, "Expired"),
            (ContractStatus.TERMINATED, "Terminated"),
        ]:
            ContractStatus.objects.get_or_create(name=status_name, defaults={"description": description})

        for status_name, description in [
            (RequestStatus.PENDING, "Pending"),
            (RequestStatus.UNDER_REVIEW, "Under review"),
            (RequestStatus.APPROVED, "Approved"),
            (RequestStatus.REVISION_REQUIRED, "Revision required"),
            (RequestStatus.REJECTED, "Rejected"),
        ]:
            RequestStatus.objects.get_or_create(name=status_name, defaults={"description": description})

        for alert_name, description in [
            (AlertType.CONTRACT_EXPIRING, "Contract is expiring soon"),
            (AlertType.CONTRACT_EXPIRED, "Contract is expired"),
            (AlertType.REQUEST_WAITING_REVIEW, "Request waits for review"),
        ]:
            AlertType.objects.get_or_create(name=alert_name, defaults={"description": description})

        for source_name, description in [
            (ProductSupplierSource.MANUAL, "Manual creation"),
            (ProductSupplierSource.REQUEST, "From supplier request"),
            (ProductSupplierSource.IMPORT, "Imported"),
            (ProductSupplierSource.API, "API"),
        ]:
            ProductSupplierSource.objects.get_or_create(name=source_name, defaults={"description": description})

        for doc_name, description in [
            (DocumentType.CONTRACT, "Contract"),
            (DocumentType.ACT, "Act"),
            (DocumentType.INVOICE, "Invoice"),
            (DocumentType.WAYBILL, "Waybill"),
            (DocumentType.CERTIFICATE, "Certificate"),
            (DocumentType.LICENSE, "License"),
            (DocumentType.OTHER, "Other"),
        ]:
            DocumentType.objects.get_or_create(name=doc_name, defaults={"description": description})

        supplier, _ = Supplier.objects.get_or_create(
            name="Sneaker Prime Supplier",
            defaults={
                "inn": "7701234567",
                "kpp": "770101001",
                "ogrn": "1027700132195",
                "legal_address": "Moscow, Demo st, 1",
                "actual_address": "Moscow, Demo st, 1",
                "phone": "+74950000000",
                "email": "supplier@example.com",
                "contact_person": "Ivan Petrov",
                "contact_phone": "+79000000001",
                "user": users["supplier_user"],
            },
        )
        if supplier.user_id != users["supplier_user"].id:
            supplier.user = users["supplier_user"]
            supplier.save(update_fields=["user"])

        active_contract_status = ContractStatus.objects.get(name=ContractStatus.ACTIVE)
        contract, _ = SupplierContract.objects.get_or_create(
            supplier=supplier,
            contract_number="SP-2026-001",
            defaults={
                "status": active_contract_status,
                "title": "Main supply contract",
                "description": "Demo contract for API checks",
                "start_date": timezone.now().date() - timedelta(days=90),
                "end_date": timezone.now().date() + timedelta(days=365),
                "total_amount": Decimal("5000000.00"),
                "is_auto_renew": True,
            },
        )

        contract_doc_type = DocumentType.objects.get(name=DocumentType.CONTRACT)
        if not ContractDocument.objects.filter(contract=contract, file_name="contract-demo.txt").exists():
            ContractDocument.objects.create(
                contract=contract,
                document_type=contract_doc_type,
                file=ContentFile(b"Demo contract file", name="contract-demo.txt"),
                file_name="contract-demo.txt",
                uploaded_by=users["admin"],
            )

        approved_request_status = RequestStatus.objects.get(name=RequestStatus.APPROVED)
        supplier_request, _ = SupplierProductRequest.objects.get_or_create(
            supplier=supplier,
            product_name="Air Zoom Nova",
            defaults={
                "manager": users["manager"],
                "status": approved_request_status,
                "category": "men",
                "product_sku": "REQ-MEN-001",
                "product_description": "Demo supplier request",
                "product_images": ["https://example.com/demo-image-1.jpg"],
                "quantity": 30,
                "suggested_price": Decimal("6200.00"),
                "suggested_old_price": Decimal("7900.00"),
                "notes": "Approved for demo",
                "reviewed_by": users["manager"],
                "reviewed_at": timezone.now(),
                "review_comment": "Looks good",
            },
        )

        invoice_doc_type = DocumentType.objects.get(name=DocumentType.INVOICE)
        if not RequestDocument.objects.filter(request=supplier_request, file_name="request-invoice.txt").exists():
            RequestDocument.objects.create(
                request=supplier_request,
                document_type=invoice_doc_type,
                file=ContentFile(b"Demo request invoice", name="request-invoice.txt"),
                file_name="request-invoice.txt",
                uploaded_by=users["supplier_user"],
            )

        RequestCommunication.objects.get_or_create(
            request=supplier_request,
            sender=users["manager"],
            direction=RequestCommunication.FROM_MANAGER,
            message="Please confirm shipment date.",
        )
        RequestCommunication.objects.get_or_create(
            request=supplier_request,
            sender=users["supplier_user"],
            direction=RequestCommunication.FROM_SUPPLIER,
            message="Shipment is planned for next Monday.",
        )

        alert_type = AlertType.objects.get(name=AlertType.REQUEST_WAITING_REVIEW)
        SystemAlert.objects.get_or_create(
            alert_type=alert_type,
            title="Supplier request reviewed",
            message="Demo supplier request is approved and ready.",
            request=supplier_request,
            contract=contract,
        )

        return {
            "supplier": supplier,
            "contract": contract,
            "source": ProductSupplierSource.objects.get(name=ProductSupplierSource.REQUEST),
            "request": supplier_request,
        }

    def _seed_products(self, supplier_context: dict[str, Any]) -> dict[str, Any]:
        """Создает категории, товары, слайдер и связь товара с поставщиком."""
        categories: dict[str, Category] = {}
        for slug, name in [
            ("women", "Кроссовки для женщин"),
            ("men", "Кроссовки для мужчин"),
            ("children", "Кроссовки для детей"),
        ]:
            category, _ = Category.objects.get_or_create(name=name, defaults={"description": f"Demo {slug} category"})
            categories[slug] = category

        filter_options = self._seed_filter_options(categories)

        products: list[Product] = []
        product_specs = [
            {
                "page": "women",
                "prefix": "W",
                "name": "Air Bloom",
                "price": Decimal("5900.00"),
                "old_price": Decimal("7600.00"),
                "filters": {
                    "colors": "white",
                    "sizes": "36",
                    "fabrics": "mesh",
                    "brands": "nova",
                    "styles": "running",
                    "seasons": "summer",
                    "purposes": "daily",
                },
            },
            {
                "page": "women",
                "prefix": "W",
                "name": "City Lace",
                "price": Decimal("6400.00"),
                "old_price": Decimal("8100.00"),
                "filters": {
                    "colors": "black",
                    "sizes": "37",
                    "fabrics": "leather",
                    "brands": "aurora",
                    "styles": "casual",
                    "seasons": "all-season",
                    "purposes": "city",
                },
            },
            {
                "page": "women",
                "prefix": "W",
                "name": "Nova Cloud",
                "price": Decimal("6700.00"),
                "old_price": Decimal("8400.00"),
                "filters": {
                    "colors": "blue",
                    "sizes": "38",
                    "fabrics": "textile",
                    "brands": "pulse",
                    "styles": "sport",
                    "seasons": "spring",
                    "purposes": "training",
                },
            },
            {
                "page": "women",
                "prefix": "W",
                "name": "Rose Drift",
                "price": Decimal("6200.00"),
                "old_price": Decimal("7900.00"),
                "filters": {
                    "colors": "red",
                    "sizes": "39",
                    "fabrics": "synthetic",
                    "brands": "vibe",
                    "styles": "fashion",
                    "seasons": "summer",
                    "purposes": "travel",
                },
            },
            {
                "page": "women",
                "prefix": "W",
                "name": "Soft Pulse",
                "price": Decimal("7100.00"),
                "old_price": Decimal("8900.00"),
                "filters": {
                    "colors": "gray",
                    "sizes": "40",
                    "fabrics": "suede",
                    "brands": "eclipse",
                    "styles": "retro",
                    "seasons": "autumn",
                    "purposes": "city",
                },
            },
            {
                "page": "women",
                "prefix": "W",
                "name": "Sand Sprint",
                "price": Decimal("6800.00"),
                "old_price": Decimal("8500.00"),
                "filters": {
                    "colors": "beige",
                    "sizes": "41",
                    "fabrics": "cotton",
                    "brands": "nova",
                    "styles": "minimal",
                    "seasons": "all-season",
                    "purposes": "daily",
                },
            },
            {
                "page": "men",
                "prefix": "M",
                "name": "Turbo Edge",
                "price": Decimal("7200.00"),
                "old_price": Decimal("9100.00"),
                "filters": {
                    "colors": "black",
                    "sizes": "41",
                    "fabrics": "mesh",
                    "brands": "strike",
                    "styles": "running",
                    "seasons": "summer",
                    "purposes": "training",
                },
            },
            {
                "page": "men",
                "prefix": "M",
                "name": "Street Alpha",
                "price": Decimal("7600.00"),
                "old_price": Decimal("9500.00"),
                "filters": {
                    "colors": "white",
                    "sizes": "42",
                    "fabrics": "leather",
                    "brands": "vector",
                    "styles": "casual",
                    "seasons": "all-season",
                    "purposes": "city",
                },
            },
            {
                "page": "men",
                "prefix": "M",
                "name": "Vector Run",
                "price": Decimal("7900.00"),
                "old_price": Decimal("9800.00"),
                "filters": {
                    "colors": "blue",
                    "sizes": "43",
                    "fabrics": "synthetic",
                    "brands": "bolt",
                    "styles": "sport",
                    "seasons": "spring",
                    "purposes": "running",
                },
            },
            {
                "page": "men",
                "prefix": "M",
                "name": "Ever Trail",
                "price": Decimal("8300.00"),
                "old_price": Decimal("10300.00"),
                "filters": {
                    "colors": "green",
                    "sizes": "44",
                    "fabrics": "suede",
                    "brands": "summit",
                    "styles": "outdoor",
                    "seasons": "autumn",
                    "purposes": "travel",
                },
            },
            {
                "page": "men",
                "prefix": "M",
                "name": "Urban Shift",
                "price": Decimal("7500.00"),
                "old_price": Decimal("9400.00"),
                "filters": {
                    "colors": "gray",
                    "sizes": "42",
                    "fabrics": "cotton",
                    "brands": "core",
                    "styles": "minimal",
                    "seasons": "all-season",
                    "purposes": "daily",
                },
            },
            {
                "page": "men",
                "prefix": "M",
                "name": "Sprint Zone",
                "price": Decimal("7700.00"),
                "old_price": Decimal("9600.00"),
                "filters": {
                    "colors": "red",
                    "sizes": "43",
                    "fabrics": "textile",
                    "brands": "strike",
                    "styles": "fashion",
                    "seasons": "winter",
                    "purposes": "city",
                },
            },
            {
                "page": "children",
                "prefix": "C",
                "name": "Kid Flash",
                "price": Decimal("4100.00"),
                "old_price": Decimal("5200.00"),
                "filters": {
                    "colors": "white",
                    "sizes": "33",
                    "fabrics": "mesh",
                    "brands": "junior",
                    "styles": "sport",
                    "seasons": "summer",
                    "purposes": "school",
                },
            },
            {
                "page": "children",
                "prefix": "C",
                "name": "Jump Mini",
                "price": Decimal("4300.00"),
                "old_price": Decimal("5400.00"),
                "filters": {
                    "colors": "blue",
                    "sizes": "34",
                    "fabrics": "textile",
                    "brands": "rookie",
                    "styles": "casual",
                    "seasons": "spring",
                    "purposes": "playground",
                },
            },
            {
                "page": "children",
                "prefix": "C",
                "name": "Play Dash",
                "price": Decimal("4500.00"),
                "old_price": Decimal("5600.00"),
                "filters": {
                    "colors": "red",
                    "sizes": "35",
                    "fabrics": "synthetic",
                    "brands": "tiny-step",
                    "styles": "running",
                    "seasons": "all-season",
                    "purposes": "sports",
                },
            },
            {
                "page": "children",
                "prefix": "C",
                "name": "Rocket Step",
                "price": Decimal("4700.00"),
                "old_price": Decimal("5900.00"),
                "filters": {
                    "colors": "black",
                    "sizes": "36",
                    "fabrics": "leather",
                    "brands": "junior",
                    "styles": "outdoor",
                    "seasons": "autumn",
                    "purposes": "school",
                },
            },
            {
                "page": "children",
                "prefix": "C",
                "name": "School Move",
                "price": Decimal("4600.00"),
                "old_price": Decimal("5800.00"),
                "filters": {
                    "colors": "gray",
                    "sizes": "37",
                    "fabrics": "cotton",
                    "brands": "rookie",
                    "styles": "minimal",
                    "seasons": "winter",
                    "purposes": "daily",
                },
            },
            {
                "page": "children",
                "prefix": "C",
                "name": "Young Comet",
                "price": Decimal("4800.00"),
                "old_price": Decimal("6100.00"),
                "filters": {
                    "colors": "green",
                    "sizes": "38",
                    "fabrics": "mesh",
                    "brands": "tiny-step",
                    "styles": "fashion",
                    "seasons": "summer",
                    "purposes": "playground",
                },
            },
        ]
        images_per_product = 3
        target_skus = {
            f"DEMO-{spec['prefix']}-{idx:03d}" for idx, spec in enumerate(product_specs, start=1)
        }

        Product.objects.filter(sku__startswith="DEMO-").exclude(sku__in=target_skus).delete()

        for idx, spec in enumerate(product_specs, start=1):
            page = spec["page"]
            prefix = spec["prefix"]
            sku = f"DEMO-{prefix}-{idx:03d}"
            product_image_urls = [
                SNEAKER_IMAGE_URLS[((idx - 1) * images_per_product + img_idx) % len(SNEAKER_IMAGE_URLS)]
                for img_idx in range(images_per_product)
            ]
            product, _ = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": spec["name"],
                    "description": f"Demo product for {page} page.",
                    "price": spec["price"],
                    "old_price": spec["old_price"],
                    "stock_quantity": 20 + idx,
                    "status": "active",
                    "is_active": True,
                    "warehouse_date": timezone.now().date() - timedelta(days=10 * idx),
                    "supplier": supplier_context["supplier"],
                    "contract": supplier_context["contract"],
                    "created_from_source": supplier_context["source"],
                    "created_from_request": supplier_context["request"] if idx == 7 else None,
                    "published_pages": [page],
                    "external_url": f"https://example.com/products/{sku.lower()}",
                },
            )
            product.categories.set([categories[page]])
            self._set_product_filters(product, filter_options, page, spec["filters"])
            self._ensure_product_images(product, product_image_urls)
            products.append(product)

        # Полностью пересобираем слайдер: удаляем старые записи и создаем только новый набор.
        SliderImage.objects.all().delete()
        slider_items = products[: len(SLIDER_SEED_FILENAMES)]
        if not slider_items:
            slider_items = products[:3]

        for idx, product in enumerate(slider_items, start=1):
            image_content, image_name = self._build_slider_image_content(idx, product)
            SliderImage.objects.create(
                title=f"Demo slide {idx}",
                description=f"Featured {product.name}",
                image=ContentFile(image_content, name=image_name),
                product=product,
                price=product.price,
                old_price=product.old_price,
                link=f"https://example.com/slider/{product.sku.lower()}",
                is_active=True,
                order=idx,
            )

        SupplierProduct.objects.get_or_create(
            supplier=supplier_context["supplier"],
            product=products[0],
            defaults={
                "contract": supplier_context["contract"],
                "supplier_sku": "SUP-DEMO-001",
                "supplier_price": Decimal("4600.00"),
                "is_preferred": True,
            },
        )

        return {"categories": categories, "products": products}

    def _seed_filter_options(
        self, categories: dict[str, Category]
    ) -> dict[str, dict[str, dict[str, FilterOption]]]:
        """Создает группы фильтров и опции по каждой категории каталога."""
        group_specs = [
            ("Цвет", "colors", {"women": ["white", "black", "blue", "red", "gray", "beige"], "men": ["black", "white", "blue", "red", "gray", "green"], "children": ["white", "blue", "red", "black", "gray", "green"]}),
            ("Размер", "sizes", {"women": ["36", "37", "38", "39", "40", "41"], "men": ["40", "41", "42", "43", "44", "45"], "children": ["33", "34", "35", "36", "37", "38"]}),
            ("Материал", "fabrics", {"women": ["mesh", "leather", "textile", "cotton", "synthetic", "suede"], "men": ["mesh", "leather", "textile", "cotton", "synthetic", "suede"], "children": ["mesh", "leather", "textile", "cotton", "synthetic", "suede"]}),
            ("Бренд", "brands", {"women": ["nova", "aurora", "pulse", "vibe", "eclipse"], "men": ["strike", "vector", "bolt", "summit", "core"], "children": ["junior", "rookie", "tiny-step", "spark"]}),
            ("Стиль", "styles", {"women": ["running", "casual", "sport", "fashion", "retro", "minimal"], "men": ["running", "casual", "sport", "fashion", "outdoor", "minimal"], "children": ["running", "casual", "sport", "fashion", "outdoor", "minimal"]}),
            ("Сезон", "seasons", {"women": ["summer", "spring", "autumn", "winter", "all-season"], "men": ["summer", "spring", "autumn", "winter", "all-season"], "children": ["summer", "spring", "autumn", "winter", "all-season"]}),
            ("Назначение", "purposes", {"women": ["daily", "city", "training", "travel"], "men": ["daily", "city", "training", "running", "travel"], "children": ["daily", "school", "sports", "playground"]}),
        ]

        options: dict[str, dict[str, dict[str, FilterOption]]] = {slug: {} for slug in categories}

        for order, (group_name, group_key, page_values) in enumerate(group_specs, start=1):
            for page_slug, category in categories.items():
                group, _ = FilterGroup.objects.get_or_create(
                    name=group_name,
                    category=category,
                    defaults={"order": order, "is_active": True},
                )
                if group.order != order or not group.is_active:
                    group.order = order
                    group.is_active = True
                    group.save(update_fields=["order", "is_active"])

                options[page_slug][group_key] = {}
                for value_order, value_name in enumerate(page_values[page_slug], start=1):
                    option, _ = FilterOption.objects.get_or_create(
                        group=group,
                        name=value_name,
                        defaults={"order": value_order, "is_active": True},
                    )
                    if option.order != value_order or not option.is_active:
                        option.order = value_order
                        option.is_active = True
                        option.save(update_fields=["order", "is_active"])
                    options[page_slug][group_key][value_name] = option

        return options

    def _set_product_filters(
        self,
        product: Product,
        filter_options: dict[str, dict[str, dict[str, FilterOption]]],
        page_slug: str,
        selected_filters: dict[str, str],
    ) -> None:
        """Полностью обновляет связи товара с фильтрами по переданному набору значений."""
        ProductFilter.objects.filter(product=product).delete()

        page_options = filter_options.get(page_slug, {})
        for group_key, selected_value in selected_filters.items():
            option = page_options.get(group_key, {}).get(selected_value)
            if option is not None:
                ProductFilter.objects.get_or_create(product=product, filter_option=option)

    def _ensure_product_images(self, product: Product, image_urls: list[str]) -> None:
        """Гарантирует наличие нескольких изображений товара с fallback на заглушку."""
        expected_count = max(1, len(image_urls))
        existing_images = list(product.images.order_by("created_at"))
        existing_names = {img.image.name.rsplit("/", 1)[-1] for img in existing_images if img.image}

        if len(existing_images) >= expected_count:
            if not any(img.is_main for img in existing_images):
                first_image = existing_images[0]
                first_image.is_main = True
                first_image.save(update_fields=["is_main"])
            return

        for img_idx, image_url in enumerate(image_urls, start=1):
            image_bytes, extension = self._download_image_bytes(image_url)
            file_name = f"{product.sku.lower()}-{img_idx}.{extension}"
            if file_name in existing_names:
                continue

            ProductImage.objects.create(
                product=product,
                image=ContentFile(image_bytes, name=file_name),
                is_main=(img_idx == 1 and not existing_images),
                alt_text=f"{product.name} photo {img_idx}",
            )

        if not product.images.filter(is_main=True).exists():
            first_image = product.images.order_by("created_at").first()
            if first_image is not None:
                first_image.is_main = True
                first_image.save(update_fields=["is_main"])

    def _download_image_bytes(self, image_url: str) -> tuple[bytes, str]:
        """Скачивает изображение; при сбое возвращает PNG-заглушку."""
        request = Request(image_url, headers={"User-Agent": "Mozilla/5.0 (demo seeder)"})
        try:
            with urlopen(request, timeout=20) as response:
                content = response.read()
                content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip()
        except (URLError, HTTPError, TimeoutError, ValueError):
            return base64.b64decode(TINY_PNG_B64), "png"

        if not content:
            return base64.b64decode(TINY_PNG_B64), "png"

        return content, self._guess_extension(image_url, content_type)

    def _guess_extension(self, image_url: str, content_type: str) -> str:
        """Определяет расширение для файла изображения."""
        mime_extension = mimetypes.guess_extension(content_type or "") or ""
        if mime_extension in {".jpg", ".jpeg", ".png", ".webp"}:
            return "jpg" if mime_extension == ".jpeg" else mime_extension.lstrip(".")

        parsed_url = urlparse(image_url)
        path_extension = parsed_url.path.rsplit(".", 1)[-1].lower() if "." in parsed_url.path else ""
        if path_extension in {"jpg", "jpeg", "png", "webp"}:
            return "jpg" if path_extension == "jpeg" else path_extension

        query_params = parse_qs(parsed_url.query)
        for key in ("fm", "format", "ext"):
            query_value = query_params.get(key, [""])[0].lower()
            if query_value in {"jpg", "jpeg", "png", "webp"}:
                return "jpg" if query_value == "jpeg" else query_value

        return "jpg"

    def _build_slider_image_content(self, slide_index: int, product: Product) -> tuple[bytes, str]:
        """Возвращает контент для слайда: сначала локальный asset, затем фото товара, затем fallback."""
        seed_file_name = SLIDER_SEED_FILENAMES[(slide_index - 1) % len(SLIDER_SEED_FILENAMES)]
        seed_file_path = SLIDER_SEED_ASSETS_DIR / seed_file_name
        if seed_file_path.exists() and seed_file_path.is_file():
            return seed_file_path.read_bytes(), seed_file_name

        product_main_image = product.images.filter(is_main=True).order_by("created_at").first() or product.images.order_by(
            "created_at"
        ).first()
        if product_main_image and product_main_image.image:
            try:
                with product_main_image.image.open("rb") as image_file:
                    ext = Path(product_main_image.image.name).suffix.lower() or ".jpg"
                    normalized_ext = ext if ext in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
                    normalized_ext = ".jpg" if normalized_ext == ".jpeg" else normalized_ext
                    return image_file.read(), f"slide-{slide_index}{normalized_ext}"
            except OSError:
                pass

        return base64.b64decode(TINY_PNG_B64), f"slide-{slide_index}.png"

    def _seed_cart_and_orders(self, users: dict[str, Any], product_context: dict[str, Any]) -> None:
        """Создает демо-корзины, статусы заказов и тестовые заказы."""
        products = product_context["products"]

        for user_key in ["buyer", "buyer_new", "other"]:
            Cart.objects.get_or_create(user=users[user_key])

        buyer_cart = users["buyer"].cart
        CartItem.objects.get_or_create(cart=buyer_cart, product=products[0], defaults={"quantity": 1})

        statuses = {}
        for name, description, is_final in [
            ("new", "New order", False),
            ("paid", "Paid", False),
            ("delivered", "Delivered", True),
            ("completed", "Completed", True),
            ("cancelled", "Cancelled", True),
        ]:
            status, _ = OrderStatus.objects.get_or_create(name=name, defaults={"description": description, "is_final": is_final})
            if status.description != description or status.is_final != is_final:
                status.description = description
                status.is_final = is_final
                status.save(update_fields=["description", "is_final"])
            statuses[name] = status

        self._create_order_if_missing(
            user=users["buyer"],
            status=statuses["paid"],
            shipping_address="Тверская улица, д 10, Москва, 101000",
            product_lines=[(products[0], 1), (products[2], 1)],
        )
        self._create_order_if_missing(
            user=users["buyer"],
            status=statuses["completed"],
            shipping_address="Ленина проспект, д 15, Санкт-Петербург, 190000",
            product_lines=[(products[1], 1)],
        )
        self._create_order_if_missing(
            user=users["other"],
            status=statuses["new"],
            shipping_address="Советская улица, д 5, Казань, 420000",
            product_lines=[(products[4], 2)],
        )

    def _create_order_if_missing(
        self,
        *,
        user: Any,
        status: OrderStatus,
        shipping_address: str,
        product_lines: list[tuple[Product, int]],
    ) -> None:
        """Создает заказ при отсутствии дубля и добавляет в него позиции."""
        order = (
            Order.objects.filter(user=user, status=status, shipping_address=shipping_address)
            .order_by("id")
            .first()
        )
        if order is None:
            order = Order.objects.create(user=user, status=status, shipping_address=shipping_address, total=Decimal("1.00"))

        for product, quantity in product_lines:
            OrderItem.objects.get_or_create(
                order=order,
                product=product,
                defaults={
                    "product_name": product.name,
                    "product_sku": product.sku,
                    "price": product.price,
                    "quantity": quantity,
                },
            )

        order.calculate_total()

    def _seed_reviews(self, users: dict[str, Any], product_context: dict[str, Any]) -> None:
        """Добавляет демонстрационные отзывы от пользователей с покупками."""
        products = product_context["products"]

        Review.objects.get_or_create(
            user=users["buyer"],
            product=products[0],
            defaults={
                "rating": 5,
                "comment": "Excellent quality and comfort.",
                "is_moderated": True,
                "is_verified_purchase": True,
            },
        )
        Review.objects.get_or_create(
            user=users["other"],
            product=products[4],
            defaults={
                "rating": 4,
                "comment": "Good for daily walks.",
                "is_moderated": False,
                "is_verified_purchase": True,
            },
        )

    def _seed_favorites(self, users: dict[str, Any], product_context: dict[str, Any]) -> None:
        """Заполняет избранное пользователей для проверки API favorites."""
        products = product_context["products"]
        ProductFavorite.objects.get_or_create(user=users["buyer"], product=products[0])
        ProductFavorite.objects.get_or_create(user=users["buyer"], product=products[2])
        ProductFavorite.objects.get_or_create(user=users["buyer_new"], product=products[1])
