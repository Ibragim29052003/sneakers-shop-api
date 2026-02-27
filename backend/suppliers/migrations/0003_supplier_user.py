# Сгенерированная миграция для добавления поля user к Supplier

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('suppliers', '0002_supplierproduct_contract_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='supplier_profile',
                to=settings.AUTH_USER_MODEL,
                verbose_name='аккаунт пользователя'
            ),
        ),
    ]
