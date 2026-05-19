from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(
                check=Q(total__gt=0),
                name='order_total_gt_0',
            ),
        ),
    ]
