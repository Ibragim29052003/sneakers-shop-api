"""
Management command для проверки истекающих договоров
Создаёт системные уведомления для договоров, которые истекают в течение 30 дней
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from suppliers.models import (
    SupplierContract,
    SystemAlert,
    AlertType,
    ContractStatus
)


class Command(BaseCommand):
    """
    Проверка договоров на истечение срока действия
    
    Ищет договоры с датой окончания менее чем через 30 дней
    и создаёт системные уведомления для них.
    
    Использование:
        python manage.py check_contract_expiration
        python manage.py check_contract_expiration --days=60
        python manage.py check_contract_expiration --dry-run
    """
    
    help = 'Проверяет договоры на истечение срока и создаёт уведомления'
    
    def add_arguments(self, parser):
        # Добавляем аргумент для количества дней
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Количество дней для проверки истечения (по умолчанию: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать уведомления, которые будут созданы, без их создания'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Вычисляем дату истечения
        expiration_date = timezone.now().date() + timedelta(days=days)
        
        self.stdout.write(
            self.style.WARNING(f'\nПроверка договоров, истекающих до {expiration_date}')
        )
        self.stdout.write(f'Порог: {days} дней\n')
        
        # Получаем активные статусы договора
        active_statuses = ContractStatus.objects.filter(
            name__in=[ContractStatus.ACTIVE, ContractStatus.DRAFT]
        )
        
        # Находим договоры, которые истекают в указанный период
        expiring_contracts = SupplierContract.objects.filter(
            status__in=active_statuses,
            end_date__lte=expiration_date,
            end_date__gte=timezone.now().date()
        ).select_related('supplier', 'status')
        
        # Также находим уже истёкшие договоры
        expired_contracts = SupplierContract.objects.filter(
            status__name=ContractStatus.ACTIVE,
            end_date__lt=timezone.now().date()
        ).select_related('supplier', 'status')
        
        # Обрабатываем истекающие договоры
        created_count = 0
        skipped_count = 0
        
        # Получаем типы уведомлений
        try:
            expiring_alert_type = AlertType.objects.get(
                name=AlertType.CONTRACT_EXPIRING
            )
            expired_alert_type = AlertType.objects.get(
                name=AlertType.CONTRACT_EXPIRED
            )
        except AlertType.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка: не найдены типы уведомлений. Запустите миграцию: {e}')
            )
            return
        
        # Обработка истекающих договоров (через 30 дней)
        for contract in expiring_contracts:
            days_until = (contract.end_date - timezone.now().date()).days
            
            # Проверяем, не создано ли уже уведомление
            existing_alert = SystemAlert.objects.filter(
                contract=contract,
                alert_type=expiring_alert_type,
                is_read=False
            ).exists()
            
            if existing_alert:
                skipped_count += 1
                self.stdout.write(
                    f'  Пропущено (уведомление уже существует): {contract.contract_number}'
                )
                continue
            
            if dry_run:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f'  [DRY-RUN] Будет создано уведомление для: '
                        f'{contract.contract_number} ({contract.supplier.name}) - '
                        f'осталось {days_until} дней'
                    )
                )
                continue
            
            # Создаём уведомление
            alert = SystemAlert.objects.create(
                alert_type=expiring_alert_type,
                title=f'Договор истекает: {contract.contract_number}',
                message=(
                    f'Договор №{contract.contract_number} с поставщиком '
                    f'"{contract.supplier.name}" истекает через {days_until} дней '
                    f'({contract.end_date}). Необходимо продлить или перезаключить договор.'
                ),
                contract=contract
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Создано уведомление: {contract.contract_number} '
                    f'(осталось {days_until} дней)'
                )
            )
        
        # Обработка истёкших договоров
        for contract in expired_contracts:
            days_ago = (timezone.now().date() - contract.end_date).days
            
            # Проверяем, не создано ли уже уведомление
            existing_alert = SystemAlert.objects.filter(
                contract=contract,
                alert_type=expired_alert_type,
                is_read=False
            ).exists()
            
            if existing_alert:
                skipped_count += 1
                self.stdout.write(
                    f'  Пропущено (уведомление уже существует): {contract.contract_number}'
                )
                continue
            
            if dry_run:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f'  [DRY-RUN] Будет создано уведомление для истёкшего: '
                        f'{contract.contract_number} ({contract.supplier.name}) - '
                        f'истёк {days_ago} дней назад'
                    )
                )
                continue
            
            # Создаём уведомление
            alert = SystemAlert.objects.create(
                alert_type=expired_alert_type,
                title=f'Договор истёк: {contract.contract_number}',
                message=(
                    f'Договор №{contract.contract_number} с поставщиком '
                    f'"{contract.supplier.name}" истёк {days_ago} дней назад '
                    f'({contract.end_date}). Необходимо срочно перезаключить договор!'
                ),
                contract=contract
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Создано уведомление об истечении: {contract.contract_number} '
                    f'(истёк {days_ago} дней назад)'
                )
            )
        
        # Итоговая статистика
        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(
                self.style.HTTP_INFO(f'Режим проверки: найдено {created_count} договоров для уведомления')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Создано уведомлений: {created_count}')
            )
        
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Пропущено (уже есть уведомления): {skipped_count}')
            )
        
        self.stdout.write('=' * 50)
