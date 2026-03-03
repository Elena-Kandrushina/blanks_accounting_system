from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from blanks.models import Blank, BlankCategory
from products.models import Product, ProductCategory, ConsumptionNorm
from warehouse.models import Warehouse, StockBalance, StockMovement
from production.models import ProductionSite, BlankReceipt, AssemblyReport, SiteBalance
from quality_control.models import DefectType, DefectReport

User = get_user_model()


class Command(BaseCommand):
    help = "Очищает все данные в проекте (включая участки и склады)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Принудительная очистка без подтверждения",
        )
        parser.add_argument(
            "--keep-users",
            action="store_true",
            help="Не удалять обычных пользователей",
        )
        parser.add_argument(
            "--keep-warehouses",
            action="store_true",
            help="Не удалять склады",
        )
        parser.add_argument(
            "--keep-sites",
            action="store_true",
            help="Не удалять производственные участки",
        )

    def handle(self, *args, **options):
        force = options["force"]
        keep_users = options["keep_users"]
        keep_warehouses = options["keep_warehouses"]
        keep_sites = options["keep_sites"]

        if not force:
            self.stdout.write(
                self.style.WARNING(
                    "ВНИМАНИЕ! Эта команда удалит ВСЕ данные в проекте:\n"
                    "- Склады и остатки\n"
                    "- Производственные участки\n"
                    "- Заготовки и изделия\n"
                    "- Заявки, отчеты, акты о браке\n"
                    "- Движения и перемещения\n"
                    f"{'- Обычных пользователей' if not keep_users else ''}\n"
                    f"{'- Склады' if not keep_warehouses else '(склады сохранятся)'}\n"
                    f"{'- Участки' if not keep_sites else '(участки сохранятся)'}"
                )
            )
            answer = input("Вы уверены? (yes/no): ")
            if answer.lower() != "yes":
                self.stdout.write(self.style.SUCCESS("Операция отменена"))
                return

        self.stdout.write("Начинаем очистку данных...")

        deleted_counts = {}

        # удаляем зависимые данные (у которых есть внешние ключи)
        models_to_delete = [
            ("Движения", StockMovement),
            ("Акты о браке", DefectReport),
            ("Отчеты о сборке", AssemblyReport),
            ("Заявки на выдачу", BlankReceipt),
            ("Остатки на участках", SiteBalance),
            ("Остатки на складах", StockBalance),
            ("Нормы расхода", ConsumptionNorm),
            ("Изделия", Product),
            ("Категории изделий", ProductCategory),
            ("Заготовки", Blank),
            ("Категории заготовок", BlankCategory),
            ("Виды брака", DefectType),
        ]

        for name, model in models_to_delete:
            count = model.objects.all().delete()[0]
            deleted_counts[name] = count
            self.stdout.write(f"  ✓ Удалено {name}: {count}")

        # Удаляем производственные участки (если не запрещено)
        if not keep_sites:
            count = ProductionSite.objects.all().delete()[0]
            deleted_counts["Производственные участки"] = count
            self.stdout.write(f"  ✓ Удалено производственных участков: {count}")
        else:
            self.stdout.write("  • Производственные участки сохранены")

        # Удаляем склады (если не запрещено)
        if not keep_warehouses:
            count = Warehouse.objects.all().delete()[0]
            deleted_counts["Склады"] = count
            self.stdout.write(f"  ✓ Удалено складов: {count}")
        else:
            self.stdout.write("  • Склады сохранены")

        # удаление обычных пользователей
        if not keep_users:
            users = User.objects.filter(is_superuser=False)
            count = users.delete()[0]
            deleted_counts["Обычные пользователи"] = count
            self.stdout.write(f"  ✓ Удалено обычных пользователей: {count}")

        self.stdout.write(self.style.SUCCESS("\nОчистка завершена!"))
        self.stdout.write("Статистика удаленных записей:")
        for name, count in deleted_counts.items():
            if count > 0:
                self.stdout.write(f"  {name}: {count}")
