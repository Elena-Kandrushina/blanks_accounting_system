from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = "Создает группы пользователей и назначает разрешения"

    def handle(self, *args, **options):
        groups_data = {
            "Администраторы": {
                "description": "Полный доступ ко всем функциям системы",
                "permissions": "all",
            },
            "Технологи": {
                "description": "Создание заготовок, изделий и норм расхода",
                "permissions": [
                    # Заготовки
                    "add_blank",
                    "change_blank",
                    "view_blank",
                    "delete_blank",
                    "add_blankcategory",
                    "change_blankcategory",
                    "view_blankcategory",
                    # Изделия
                    "add_product",
                    "change_product",
                    "view_product",
                    "delete_product",
                    "add_productcategory",
                    "change_productcategory",
                    "view_productcategory",
                    # Нормы расхода
                    "add_consumptionnorm",
                    "change_consumptionnorm",
                    "view_consumptionnorm",
                ],
            },
            "Кладовщики": {
                "description": "Учет заготовок на складах",
                "permissions": [
                    # Склады
                    "add_warehouse",
                    "change_warehouse",
                    "view_warehouse",
                    # Остатки
                    "add_stockbalance",
                    "change_stockbalance",
                    "view_stockbalance",
                    # Движения
                    "add_stockmovement",
                    "change_stockmovement",
                    "view_stockmovement",
                    # Просмотр
                    "view_blank",
                    "view_product",
                ],
            },
            "Мастера участков": {
                "description": "Управление производственным участком",
                "permissions": [
                    # Поступления заготовок
                    "add_blankreceipt",
                    "change_blankreceipt",
                    "view_blankreceipt",
                    # Отчеты о сборке
                    "add_assemblyreport",
                    "view_assemblyreport",
                    # Остатки на участке
                    "view_sitebalance",
                    "change_sitebalance",
                    # Просмотр
                    "view_blank",
                    "view_product",
                    "view_consumptionnorm",
                ],
            },
            "Старшие контролеры ОТК": {
                "description": "Подтверждение брака и управление справочниками",
                "permissions": [
                    # Виды брака
                    "add_defecttype",
                    "change_defecttype",
                    "view_defecttype",
                    # Акты о браке
                    "add_defectreport",
                    "change_defectreport",
                    "view_defectreport",
                    # Подтверждение брака (списание)
                    "change_defectreport",
                    # Просмотр
                    "view_blank",
                    "view_product",
                    "view_sitebalance",
                ],
            },
        }

        for group_name, data in groups_data.items():
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Создана группа: "{group_name}"'))
            else:
                self.stdout.write(
                    self.style.WARNING(f'Обновлена группа: "{group_name}"')
                )

            self.assign_permissions(group, data["permissions"])

        self.stdout.write(
            self.style.SUCCESS("\n Все группы созданы и разрешения назначены!")
        )

    def assign_permissions(self, group, permissions_spec):
        """Назначить разрешения группе"""
        if permissions_spec == "all":
            group.permissions.set(Permission.objects.all())
            self.stdout.write(self.style.SUCCESS("Назначены все разрешения"))
            return

        group.permissions.clear()
        assigned = 0
        not_found = []

        for perm_codename in permissions_spec:
            try:
                permission = Permission.objects.get(codename=perm_codename)
                group.permissions.add(permission)
                assigned += 1
            except Permission.DoesNotExist:
                not_found.append(perm_codename)

        self.stdout.write(self.style.SUCCESS(f"Назначено {assigned} разрешений"))

        if not_found:
            self.stdout.write(
                self.style.WARNING(
                    f'Не найдены: {", ".join(not_found)}. '
                    f"Возможно, нужно сначала создать модели и сделать миграции."
                )
            )
