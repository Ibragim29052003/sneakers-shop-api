from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_total_gt_0'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='order',
            name='order_total_gt_0',
        ),
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(
                condition=Q(total__gt=0),
                name='order_total_gt_0',
            ),
        ),
    ]
