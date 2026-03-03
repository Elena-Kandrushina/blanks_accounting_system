from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from warehouse.models import Warehouse, StockBalance
from blanks.models import Blank, BlankCategory
from products.models import Product, ProductCategory, ConsumptionNorm
from production.models import ProductionSite, BlankReceipt, SiteBalance
from quality_control.models import DefectType
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми данными"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-password",
            type=str,
            default="testpass123",
            help="Пароль для тестовых пользователей (по умолчанию: testpass123)",
        )

    def handle(self, *args, **options):
        user_password = options["user_password"]

        self.stdout.write(
            self.style.SUCCESS("Начинаем заполнение тестовыми данными...")
        )

        # Создание тестовых пользователей
        self.create_test_users(user_password)

        # Создание складов
        self.create_warehouses()

        # Создание категории для заготовок
        self.create_categories()

        # Создание заготовки
        self.create_blanks()

        # Создание категории для изделий
        self.create_product_categories()

        # Создание изделия
        self.create_products()

        # Создание норм расхода
        self.create_consumption_norms()

        # Создание видов брака
        self.create_defect_types()

        # Создание производственных участков
        self.create_production_sites()

        # Создание остатков на складах
        self.create_stock_balances()

        # Создание заявки на выдачу заготовок
        self.create_blank_requests()

        self.stdout.write(self.style.SUCCESS('\n Все тестовые данные успешно созданы!'))

        # Инструкция по входу
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("ГОТОВО К ТЕСТИРОВАНИЮ!"))
        self.stdout.write("=" * 60)
        self.stdout.write("Для входа используйте:")
        self.stdout.write("Администратор: admin@example.com / (пароль от createsuperuser)")
        self.stdout.write(f"  Технолог: technologist@test.ru / {user_password}")
        self.stdout.write(f"  Кладовщик: storekeeper@test.ru / {user_password}")
        self.stdout.write(f"  Мастер участка: master@test.ru / {user_password}")
        self.stdout.write(
            f"  Старший контролер ОТК: otk_senior@test.ru / {user_password}"
        )
        self.stdout.write("=" * 60)

    def create_test_users(self, password):
        """Создание тестовых пользователей"""
        self.stdout.write("Создаем тестовых пользователей...")

        test_users = [
            {
                "email": "technologist@test.ru",
                "first_name": "Технолог",
                "last_name": "Тестов",
                "role": "technologist",
                "department": "Технологический отдел",
                "phone_number": "111-22-33",
            },
            {
                "email": "storekeeper@test.ru",
                "first_name": "Кладовщик",
                "last_name": "Складской",
                "role": "storekeeper",
                "department": "Склад №1",
                "phone_number": "222-33-44",
            },
            {
                "email": "master@test.ru",
                "first_name": "Мастер",
                "last_name": "Участков",
                "role": "production_master",
                "department": "Участок Ду 50",
                "phone_number": "333-44-55",
            },
            {
                "email": "otk_senior@test.ru",
                "first_name": "Старший",
                "last_name": "Контролер",
                "role": "otk_senior",
                "department": "ОТК",
                "phone_number": "444-55-66",
            },
        ]

        created_count = 0
        for user_data in test_users:
            if not User.objects.filter(email=user_data["email"]).exists():
                User.objects.create_user(
                    email=user_data["email"],
                    password=password,
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data["role"],
                    department=user_data["department"],
                    phone_number=user_data["phone_number"],
                    is_approved=True,
                    is_active=True,
                )
                self.stdout.write(
                    f'  Создан пользователь: {user_data["email"]} ({user_data["role"]})'
                )
                created_count += 1
            else:
                self.stdout.write(
                    f'  Пользователь уже существует: {user_data["email"]}'
                )

        self.stdout.write(f"  Создано новых пользователей: {created_count}")

    def create_warehouses(self):
        """Создание складов"""
        self.stdout.write("Создаем склады...")

        warehouses_data = [
            {
                "code": "СК-01",
                "name": "Склад заготовок",
                "address": "г. Москва, ул. Промышленная, 1",
            },
            {
                "code": "СК-02",
                "name": "Склад заготовок 2",
                "address": "г. Москва, ул. Заводская, 10",
            },
        ]

        for data in warehouses_data:
            warehouse, created = Warehouse.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "address": data["address"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(
                    f"  Создан склад: {warehouse.code} - {warehouse.name}"
                )
            else:
                self.stdout.write(f"  Склад уже существует: {warehouse.code}")

    def create_categories(self):
        """Создание категорий заготовок"""
        self.stdout.write("Создаем категории заготовок...")

        categories = ["Корпусные детали", "Крышки", "Диски", "Валы", "Шпиндели"]

        for cat_name in categories:
            category, created = BlankCategory.objects.get_or_create(
                name=cat_name, defaults={"description": f"Категория: {cat_name}"}
            )
            if created:
                self.stdout.write(f"  Создана категория: {category.name}")

    def create_blanks(self):
        """Создание заготовок"""
        self.stdout.write("Создаем заготовки...")

        blanks_data = [
            # Для Ду 50
            {"article": "0909", "name": "крышка 50-16", "unit": "шт", "weight": 2.5},
            {"article": "1111", "name": "корпус 50-16", "unit": "шт", "weight": 5.2},
            {"article": "2222", "name": "диск 50-16", "unit": "шт", "weight": 1.8},
            {"article": "3333", "name": "шпиндель 50-16", "unit": "шт", "weight": 3.2},
            # Для Ду 80
            {"article": "0808", "name": "крышка 80-16", "unit": "шт", "weight": 4.2},
            {"article": "1212", "name": "корпус 80-16", "unit": "шт", "weight": 8.5},
            {"article": "2323", "name": "диск 80-16", "unit": "шт", "weight": 3.1},
            {"article": "3434", "name": "шпиндель 80-16", "unit": "шт", "weight": 5.8},
        ]

        for data in blanks_data:
            blank, created = Blank.objects.get_or_create(
                article=data["article"],
                defaults={
                    "name": data["name"],
                    "unit": data["unit"],
                    "weight": data["weight"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(
                    f"  Создана заготовка: {blank.article} - {blank.name}"
                )
            else:
                self.stdout.write(f"  Заготовка уже существует: {blank.article}")

    def create_product_categories(self):
        """Создание категорий изделий"""
        self.stdout.write("Создаем категории изделий...")

        categories = ["Задвижки клиновые", "Краны шаровые", "Клапаны обратные"]

        for cat_name in categories:
            category, created = ProductCategory.objects.get_or_create(
                name=cat_name, defaults={"description": f"Категория: {cat_name}"}
            )
            if created:
                self.stdout.write(f"  Создана категория изделий: {category.name}")

    def create_products(self):
        """Создание изделий"""
        self.stdout.write("Создаем изделия...")

        category = ProductCategory.objects.filter(name="Задвижки клиновые").first()

        products_data = [
            {
                "article": "30с41нж-50",
                "name": "задвижка 30с41нж Ру 16 Ду 50",
                "description": "Задвижка клиновая с выдвижным шпинделем, Ру 16, Ду 50",
            },
            {
                "article": "30с41нж-80",
                "name": "задвижка 30с41нж Ру 16 Ду 80",
                "description": "Задвижка клиновая с выдвижным шпинделем, Ру 16, Ду 80",
            },
        ]

        for data in products_data:
            product, created = Product.objects.get_or_create(
                article=data["article"],
                defaults={
                    "name": data["name"],
                    "category": category,
                    "description": data["description"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(
                    f"  Создано изделие: {product.article} - {product.name}"
                )
            else:
                self.stdout.write(f"  Изделие уже существует: {product.article}")

    def create_consumption_norms(self):
        """Создание норм расхода"""
        self.stdout.write("Создаем нормы расхода...")

        product_50 = Product.objects.get(article="30с41нж-50")
        product_80 = Product.objects.get(article="30с41нж-80")

        cap_50 = Blank.objects.get(article="0909")  # крышка 50-16
        body_50 = Blank.objects.get(article="1111")  # корпус 50-16
        disc_50 = Blank.objects.get(article="2222")  # диск 50-16
        spindle_50 = Blank.objects.get(article="3333")  # шпиндель 50-16

        cap_80 = Blank.objects.get(article="0808")  # крышка 80-16
        body_80 = Blank.objects.get(article="1212")  # корпус 80-16
        disc_80 = Blank.objects.get(article="2323")  # диск 80-16
        spindle_80 = Blank.objects.get(article="3434")  # шпиндель 80-16

        # Нормы для Ду 50
        norms_data_50 = [
            {"product": product_50, "blank": cap_50, "quantity": 1},
            {"product": product_50, "blank": body_50, "quantity": 1},
            {"product": product_50, "blank": disc_50, "quantity": 2},
            {"product": product_50, "blank": spindle_50, "quantity": 1},
        ]

        # Нормы для Ду 80
        norms_data_80 = [
            {"product": product_80, "blank": cap_80, "quantity": 1},
            {"product": product_80, "blank": body_80, "quantity": 1},
            {"product": product_80, "blank": disc_80, "quantity": 2},
            {"product": product_80, "blank": spindle_80, "quantity": 1},
        ]

        # Создаем нормы для Ду 50
        for data in norms_data_50:
            norm, created = ConsumptionNorm.objects.get_or_create(
                product=data["product"],
                blank=data["blank"],
                defaults={"quantity": data["quantity"]},
            )
            if created:
                self.stdout.write(
                    f'  Создана норма: {data["product"].name} -> {data["blank"].name} = {data["quantity"]}'
                )

        # Создаем нормы для Ду 80
        for data in norms_data_80:
            norm, created = ConsumptionNorm.objects.get_or_create(
                product=data["product"],
                blank=data["blank"],
                defaults={"quantity": data["quantity"]},
            )
            if created:
                self.stdout.write(
                    f'  Создана норма: {data["product"].name} -> {data["blank"].name} = {data["quantity"]}'
                )

    def create_defect_types(self):
        """Создание видов брака для ОТК"""
        self.stdout.write("Создаем виды брака...")

        defect_types_data = [
            {"code": "ТРЕЩ", "name": "Трещина", "description": "Трещина в материале"},
            {
                "code": "СКОЛ",
                "name": "Скол",
                "description": "Скол кромки или поверхности",
            },
            {"code": "ЦАР", "name": "Царапина", "description": "Глубокая царапина"},
            {
                "code": "РАЗМ",
                "name": "Несоответствие размеров",
                "description": "Размеры вне допуска",
            },
            {
                "code": "ШЕРОХ",
                "name": "Шероховатость",
                "description": "Несоответствие шероховатости",
            },
        ]

        for data in defect_types_data:
            defect_type, created = DefectType.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(
                    f"  Создан вид брака: {defect_type.code} - {defect_type.name}"
                )

    def create_production_sites(self):
        """Создание производственных участков с привязкой к складам"""
        self.stdout.write("Создаем производственные участки...")

        # Получаем склады
        try:
            warehouse_1 = Warehouse.objects.get(code="СК-01")
            warehouse_2 = Warehouse.objects.get(code="СК-02")
        except Warehouse.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"  Ошибка: {e}"))
            self.stdout.write(self.style.ERROR("  Сначала создайте склады"))
            return

        sites_data = [
            {"code": "УЧ-01", "name": "Участок Ду 50", "warehouse": warehouse_1},
            {"code": "УЧ-02", "name": "Участок Ду 80", "warehouse": warehouse_2},
        ]

        for data in sites_data:
            site, created = ProductionSite.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "warehouse": data["warehouse"],
                    "is_active": True,
                },
            )

            if created:
                self.stdout.write(
                    f'  Создан участок: {site.code} - {site.name} (склад: {data["warehouse"].code})'
                )
            else:

                if not site.warehouse:
                    site.warehouse = data["warehouse"]
                    site.save()
                    self.stdout.write(
                        f'  Обновлен участок: {site.code} - привязан склад {data["warehouse"].code}'
                    )
                else:
                    self.stdout.write(
                        f"  Участок уже существует: {site.code} (склад: {site.warehouse.code})"
                    )

    def create_stock_balances(self):
        """Создание остатков на складах"""
        self.stdout.write("Создаем остатки на складах...")

        warehouses = Warehouse.objects.all()
        blanks = Blank.objects.all()

        for warehouse in warehouses:
            for blank in blanks:
                balance, created = StockBalance.objects.get_or_create(
                    warehouse=warehouse,
                    blank=blank,
                    defaults={"quantity": 200, "min_stock": 30},
                )
                if created:
                    self.stdout.write(
                        f"  Создан остаток: {warehouse.code} - {blank.name}: 200 шт"
                    )

    def create_blank_requests(self):
        """Создание заявок на выдачу заготовок на участки"""
        self.stdout.write("Создаем заявки на выдачу заготовок...")

        # Получаем участки
        site_50 = ProductionSite.objects.get(code="УЧ-01")
        site_80 = ProductionSite.objects.get(code="УЧ-02")

        # Получаем заготовки
        cap_50 = Blank.objects.get(article="0909")  # крышка 50-16
        body_50 = Blank.objects.get(article="1111")  # корпус 50-16
        disc_50 = Blank.objects.get(article="2222")  # диск 50-16
        spindle_50 = Blank.objects.get(article="3333")  # шпиндель 50-16

        cap_80 = Blank.objects.get(article="0808")  # крышка 80-16
        body_80 = Blank.objects.get(article="1212")  # корпус 80-16
        disc_80 = Blank.objects.get(article="2323")  # диск 80-16
        spindle_80 = Blank.objects.get(article="3434")  # шпиндель 80-16

        # Получаем мастера для создания заявок
        master = User.objects.filter(role="production_master").first()
        if not master:
            master = User.objects.first()

        now = timezone.now()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        # Заявки на участок Ду 50
        requests_data_50 = [
            {"site": site_50, "blank": cap_50, "quantity": 50, "date": yesterday},
            {"site": site_50, "blank": body_50, "quantity": 45, "date": yesterday},
            {"site": site_50, "blank": disc_50, "quantity": 100, "date": two_days_ago},
            {"site": site_50, "blank": spindle_50, "quantity": 30, "date": now},
        ]

        for data in requests_data_50:
            # Создаем заявку
            request = BlankReceipt.objects.create(
                production_site=data["site"],
                blank=data["blank"],
                quantity=data["quantity"],
                receipt_date=data["date"],
                source_info="Первоначальная заявка",
                created_by=master,
                status="new",
                comment="Тестовая заявка на выдачу",
            )
            self.stdout.write(
                f'  Создана заявка {request.number} на {data["site"].code}: {data["blank"].name} - {data["quantity"]} шт'
            )

        # Заявки на участок Ду 80
        requests_data_80 = [
            {"site": site_80, "blank": cap_80, "quantity": 30, "date": yesterday},
            {"site": site_80, "blank": body_80, "quantity": 30, "date": yesterday},
            {"site": site_80, "blank": disc_80, "quantity": 60, "date": two_days_ago},
            {"site": site_80, "blank": spindle_80, "quantity": 20, "date": now},
        ]

        for data in requests_data_80:
            request = BlankReceipt.objects.create(
                production_site=data["site"],
                blank=data["blank"],
                quantity=data["quantity"],
                receipt_date=data["date"],
                source_info="Первоначальная заявка",
                created_by=master,
                status="new",
                comment="Тестовая заявка на выдачу",
            )
            self.stdout.write(
                f'  Создана заявка {request.number} на {data["site"].code}: {data["blank"].name} - {data["quantity"]} шт'
            )

        # Проверяем созданные остатки на участках
        self.stdout.write("\n  Текущие остатки на участках после заявок:")
        for site in [site_50, site_80]:
            balances = SiteBalance.objects.filter(production_site=site)
            for balance in balances:
                self.stdout.write(
                    f"    {site.code} - {balance.blank.name}: {balance.quantity} шт"
                )
