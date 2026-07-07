"""Наполнение стенда демо-данными для проверки мобильного приложения.

Идемпотентна: повторный запуск не создаёт дублей (get_or_create по кодам).
Создаёт справочники (города, филиалы, тарифы, доп.услуги, склады с зонами и
ячейками, парк ТС), тестовые учётки всех ролей и демо-заказ с QR + рейс,
назначенный тестовому водителю.

Запуск:
    cd app && DJANGO_SETTINGS_MODULE=core.settings.dev python manage.py seed_demo
    ...              python manage.py seed_demo --wipe   # снести демо-данные

Пароль всех тестовых учёток — Passw0rd!Demo (12+ символов, сложность ок).
"""

from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.branches.models import Branch, City
from apps.orders.choices import DeliveryType, OrderStatus, PaymentType
from apps.orders.services import OrderService
from apps.orders.transitions import OrderTransitionService
from apps.packages.choices import PackageStatus
from apps.packages.services import PackageService
from apps.packages.transitions import PackageTransitionService
from apps.shipments.choices import ShipmentStatus
from apps.shipments.models import Shipment
from apps.shipments.services import ShipmentService, ShipmentTransitionService
from apps.tariffs.models import AdditionalService, Tariff
from apps.users.choices import Roles
from apps.users.models import DriverProfile, User
from apps.users.services import UserService
from apps.vehicles.choices import VehicleStatus
from apps.vehicles.models import Vehicle, VehicleType
from apps.warehouses.choices import ZoneType
from apps.warehouses.models import Warehouse, WarehouseCell, WarehouseZone

DEMO_PASSWORD = 'Passw0rd!Demo'

# (role, phone, first_name, last_name)
DEMO_USERS = [
    (Roles.SUPERADMIN, '+996700900001', 'Демо', 'Суперадмин'),
    (Roles.DIRECTOR, '+996700900002', 'Демо', 'Директор'),
    (Roles.OPERATOR, '+996700900003', 'Демо', 'Оператор'),
    (Roles.WAREHOUSE, '+996700900004', 'Демо', 'Складовщик'),
    (Roles.DRIVER, '+996700900005', 'Демо', 'Водитель'),
    (Roles.FINANCE, '+996700900006', 'Демо', 'Финансист'),
    (Roles.CLIENT, '+996700900777', 'Демо', 'Клиент'),
]

CITIES = [
    ('Бишкек', 'BIS', Decimal('42.874621'), Decimal('74.569762')),
    ('Ош', 'OSH', Decimal('40.514202'), Decimal('72.812204')),
    ('Джалал-Абад', 'JAL', Decimal('40.933393'), Decimal('72.999672')),
    ('Каракол', 'KAR', Decimal('42.490527'), Decimal('78.393604')),
]


class Command(BaseCommand):
    help = 'Наполняет стенд демо-данными для проверки мобильного приложения.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--wipe',
            action='store_true',
            help='Снести демо-данные (по демо-кодам/телефонам) вместо создания.',
        )

    def handle(self, *args, **options):
        if options['wipe']:
            self._wipe()
            return
        with transaction.atomic():
            actor = self._seed_users()
            cities = self._seed_cities(actor)
            branches = self._seed_branches(actor, cities)
            self._seed_tariffs(actor, cities)
            services = self._seed_services(actor)
            self._seed_warehouses(actor, branches)
            self._seed_fleet(actor, branches)
            self._seed_demo_order(actor, branches, services)
        self.stdout.write(self.style.SUCCESS('Демо-данные готовы. Пароль учёток: ' + DEMO_PASSWORD))

    # ------------------------------------------------------------------ users
    def _seed_users(self) -> User:
        superadmin = None
        # первый суперадмин создаётся напрямую (актора ещё нет)
        for role, phone, first, last in DEMO_USERS:
            user = User.objects.filter(phone=phone).first()
            if user is None:
                if role == Roles.SUPERADMIN and superadmin is None:
                    user = User(phone=phone, first_name=first, last_name=last, role=role, is_staff=True)
                    user.set_password(DEMO_PASSWORD)
                    user.is_verified = True
                    user.save()
                    UserService.create_profile(user)
                else:
                    actor = superadmin or User.objects.filter(role=Roles.SUPERADMIN).first()
                    user = UserService.create(
                        actor=actor,
                        phone=phone,
                        password=DEMO_PASSWORD,
                        role=role,
                        first_name=first,
                        last_name=last,
                        is_verified=True,
                    )
            if role == Roles.SUPERADMIN:
                superadmin = user
            self.stdout.write(f'  user {role:10s} {phone}')
        return superadmin

    # ----------------------------------------------------------------- cities
    def _seed_cities(self, actor) -> dict[str, City]:
        cities = {}
        for name, code, lat, lng in CITIES:
            city, _ = City.objects.get_or_create(
                code=code,
                defaults={'name': name, 'latitude': lat, 'longitude': lng, 'created_by': actor},
            )
            cities[code] = city
        self.stdout.write(f'  cities: {len(cities)}')
        return cities

    def _seed_branches(self, actor, cities) -> dict[str, Branch]:
        branches = {}
        for code, city in cities.items():
            branch, _ = Branch.objects.get_or_create(
                code=f'{code}01',
                defaults={
                    'city': city,
                    'name': f'{city.name} — центральный',
                    'address': f'{city.name}, ул. Центральная, 1',
                    'phone': '+996312000000',
                    'is_main': code == 'BIS',
                    'opening_time': time(9, 0),
                    'closing_time': time(20, 0),
                    'created_by': actor,
                },
            )
            branches[code] = branch
        self.stdout.write(f'  branches: {len(branches)}')
        return branches

    def _seed_tariffs(self, actor, cities) -> None:
        # тариф по умолчанию (любое направление)
        Tariff.objects.get_or_create(
            code='DEFAULT',
            defaults={
                'name': 'Базовый тариф',
                'from_city': None,
                'to_city': None,
                'base_price': Decimal('150'),
                'price_per_kg': Decimal('35'),
                'price_per_m3': Decimal('1200'),
                'min_price': Decimal('200'),
                'insurance_percent': Decimal('1.5'),
                'created_by': actor,
            },
        )
        routes = [('BIS', 'OSH'), ('BIS', 'JAL'), ('BIS', 'KAR'), ('OSH', 'BIS')]
        for src, dst in routes:
            Tariff.objects.get_or_create(
                code=f'{src}-{dst}',
                defaults={
                    'name': f'{cities[src].name} → {cities[dst].name}',
                    'from_city': cities[src],
                    'to_city': cities[dst],
                    'base_price': Decimal('300'),
                    'price_per_kg': Decimal('30'),
                    'price_per_m3': Decimal('1000'),
                    'min_price': Decimal('350'),
                    'insurance_percent': Decimal('1.0'),
                    'created_by': actor,
                },
            )
        self.stdout.write(f'  tariffs: {len(routes) + 1}')

    def _seed_services(self, actor) -> list[AdditionalService]:
        data = [
            ('PACKING', 'Упаковка', Decimal('150')),
            ('DOOR', 'Доставка до двери', Decimal('300')),
            ('EXPRESS', 'Экспресс-доставка', Decimal('500')),
            ('FRAGILE', 'Хрупкий груз', Decimal('200')),
        ]
        services = []
        for code, name, price in data:
            service, _ = AdditionalService.objects.get_or_create(
                code=code, defaults={'name': name, 'price': price, 'created_by': actor}
            )
            services.append(service)
        self.stdout.write(f'  services: {len(services)}')
        return services

    def _seed_warehouses(self, actor, branches) -> None:
        for code, branch in branches.items():
            warehouse, _ = Warehouse.objects.get_or_create(
                code=f'WH-{code}',
                defaults={
                    'branch': branch,
                    'name': f'Склад {branch.city.name}',
                    'total_area': Decimal('500'),
                    'max_weight': Decimal('50000'),
                    'created_by': actor,
                },
            )
            for zcode, ztype, zname in [
                ('RCV', ZoneType.RECEIVING, 'Приёмка'),
                ('STG', ZoneType.STORAGE, 'Хранение'),
                ('DSP', ZoneType.DISPATCH, 'Отгрузка'),
            ]:
                zone, _ = WarehouseZone.objects.get_or_create(
                    warehouse=warehouse,
                    code=zcode,
                    defaults={'name': zname, 'type': ztype, 'created_by': actor},
                )
                if ztype == ZoneType.STORAGE:
                    for i in range(1, 6):
                        WarehouseCell.objects.get_or_create(
                            zone=zone,
                            code=f'A-{i:02d}',
                            defaults={
                                'shelf': 'A',
                                'row': str(i),
                                'level': '1',
                                'capacity_weight': Decimal('1000'),
                                'capacity_volume': Decimal('5.000'),
                                'created_by': actor,
                            },
                        )
        self.stdout.write(f'  warehouses: {len(branches)} (+ зоны и ячейки)')

    def _seed_fleet(self, actor, branches) -> None:
        vtype, _ = VehicleType.objects.get_or_create(
            code='TRUCK5',
            defaults={
                'name': 'Грузовик 5т',
                'max_weight': Decimal('5000'),
                'max_volume': Decimal('30.000'),
                'created_by': actor,
            },
        )
        driver = User.objects.filter(role=Roles.DRIVER, phone='+996700900005').first()
        vehicle, _ = Vehicle.objects.get_or_create(
            plate_number='01KG777AAA',
            defaults={
                'vehicle_type': vtype,
                'branch': branches['BIS'],
                'brand': 'ГАЗ',
                'model': 'Газель Next',
                'year': 2022,
                'max_weight': Decimal('5000'),
                'max_volume': Decimal('30.000'),
                'status': VehicleStatus.AVAILABLE,
                'current_driver': driver,
                'created_by': actor,
            },
        )
        if driver is not None:
            DriverProfile.objects.filter(user=driver).update(assigned_vehicle=vehicle)
        self.stdout.write('  fleet: 1 тип ТС, 1 автомобиль (закреплён за водителем)')

    def _seed_demo_order(self, actor, branches, services) -> None:
        client = User.objects.filter(role=Roles.CLIENT, phone='+996700900777').first()
        driver = User.objects.filter(role=Roles.DRIVER, phone='+996700900005').first()
        if Shipment.objects.filter(shipment_number__startswith='SHP').exists() and client.orders.exists():
            self.stdout.write('  demo order/shipment: уже есть, пропуск')
            return

        order = OrderService.create(
            actor=actor,
            client=client,
            sender_name='Демо Отправитель',
            sender_phone='+996700900777',
            sender_address='Бишкек, ул. Чуй, 100',
            receiver_name='Демо Получатель',
            receiver_phone='+996700900888',
            receiver_address='Ош, ул. Ленина, 5',
            from_branch=branches['BIS'],
            to_branch=branches['OSH'],
            payment_type=PaymentType.CASH,
            delivery_type=DeliveryType.BRANCH_PICKUP,
            comment='Демо-заказ (seed_demo)',
            packages=[
                {
                    'title': 'Коробка с документами',
                    'weight': Decimal('3.500'),
                    'length': 40,
                    'width': 30,
                    'height': 20,
                    'declared_price': Decimal('5000'),
                },
                {
                    'title': 'Хрупкий груз',
                    'weight': Decimal('8.000'),
                    'length': 60,
                    'width': 40,
                    'height': 40,
                    'declared_price': Decimal('12000'),
                    'fragile': True,
                },
            ],
            services=services[:2],
        )
        for package in order.packages.all():
            PackageService.generate_qr(actor=actor, package=package)

        # Проводим заказ по FSM до готовности к отправке (склад → рейс).
        # Актор — суперадмин, входит во все ролевые наборы переходов.
        for to_status in (
            OrderStatus.WAITING_CONFIRMATION,
            OrderStatus.CONFIRMED,
            OrderStatus.WAITING_PAYMENT,
            OrderStatus.PAID,
            OrderStatus.WAITING_RECEIVE,
            OrderStatus.RECEIVED,
            OrderStatus.IN_WAREHOUSE,
            OrderStatus.WAITING_SHIPMENT,
        ):
            order = OrderTransitionService.change(order=order, to_status=to_status, actor=actor)

        vehicle = Vehicle.objects.filter(plate_number='01KG777AAA').first()
        shipment = ShipmentService.create(
            actor=actor,
            departure_branch=branches['BIS'],
            arrival_branch=branches['OSH'],
        )
        if vehicle is not None:
            ShipmentService.assign_vehicle(actor=actor, shipment=shipment, vehicle=vehicle)
        ShipmentService.assign_driver(actor=actor, shipment=shipment, driver=driver)
        # Груз проходит склад (приём → проверка → размещение) перед погрузкой
        for package in order.packages.all():
            for pkg_status in (
                PackageStatus.RECEIVED,
                PackageStatus.CHECKED,
                PackageStatus.STORED,
            ):
                PackageTransitionService.change(package=package, to_status=pkg_status, actor=actor)
        ShipmentService.add_order(actor=actor, shipment=shipment, order=order)
        # PLANNED делает рейс «активным» — заказ показывает active_shipment
        ShipmentTransitionService.change(shipment=shipment, to_status=ShipmentStatus.PLANNED, actor=actor)
        self.stdout.write(
            f'  demo order {order.order_number} (QR готовы) + рейс {shipment.shipment_number} на водителя'
        )

    # ------------------------------------------------------------------- wipe
    def _wipe(self) -> None:
        phones = [phone for _, phone, _, _ in DEMO_USERS]
        Shipment.all_objects.filter(created_by__phone__in=phones).hard_delete()
        User.all_objects.filter(phone__in=phones).hard_delete()
        self.stdout.write(self.style.WARNING('Демо-пользователи и их рейсы удалены (справочники оставлены).'))
        self.stdout.write('Заказы/грузы/справочники удаляйте вручную при необходимости (PROTECT-связи).')
