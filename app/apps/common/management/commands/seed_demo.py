"""Наполнение стенда демо-данными для проверки мобильного приложения.

Идемпотентна: повторный запуск не создаёт дублей (get_or_create по кодам).
Создаёт справочники (города, филиалы, маршруты с точками, тарифы, доп.услуги,
склады с зонами и ячейками, парк ТС), тестовые учётки всех ролей и сценарии:
заказы во всех ключевых статусах и четыре рейса (ready, in_transit с
отметками точек, arrived, completed). Всё доводится реальными операциями
сервисов, поэтому данные непротиворечивы. В конце печатает учётки, QR-коды
грузов и рейсы.

Запуск:
    cd app && DJANGO_SETTINGS_MODULE=core.settings.dev python manage.py seed_demo
    ...              python manage.py seed_demo --wipe   # снести демо-данные

Пароль всех тестовых учёток — Passw0rd!Demo (12+ символов, сложность ок).
"""

import uuid
from datetime import time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.branches.models import Branch, City
from apps.orders.choices import DeliveryType, OrderStatus, PaymentType
from apps.orders.services import OrderService
from apps.orders.transitions import OrderTransitionService
from apps.packages.choices import PackageStatus
from apps.packages.services import PackageService
from apps.packages.transitions import PackageTransitionService
from apps.orders.models import Order
from apps.packages.models import Package
from apps.routes.models import Route, RoutePoint
from apps.shipments.choices import ShipmentStatus
from apps.shipments.models import Shipment
from apps.shipments.services import (
    ShipmentCheckpointService,
    ShipmentService,
    ShipmentTransitionService,
)
from apps.tariffs.models import AdditionalService, Tariff
from apps.users.choices import Roles
from apps.users.models import DriverProfile, EmployeeProfile, User
from apps.users.services import UserService
from apps.vehicles.choices import VehicleStatus
from apps.vehicles.models import Vehicle, VehicleType
from apps.warehouses.choices import ZoneType
from apps.warehouses.models import Warehouse, WarehouseCell, WarehouseZone
from apps.warehouses.operations import WarehouseOperationsService

DEMO_PASSWORD = 'Passw0rd!Demo'

# (role, phone, first_name, last_name)
DEMO_USERS = [
    (Roles.SUPERADMIN, '+996700900001', 'Демо', 'Суперадмин'),
    (Roles.DIRECTOR, '+996700900002', 'Демо', 'Директор'),
    (Roles.OPERATOR, '+996700900003', 'Демо', 'Оператор'),
    (Roles.WAREHOUSE, '+996700900004', 'Нургуль', 'Асанова'),  # склад Бишкека
    (Roles.WAREHOUSE, '+996700900009', 'Айзада', 'Мамбетова'),  # склад Оша
    (Roles.DRIVER, '+996700900005', 'Марат', 'Кадыров'),
    (Roles.DRIVER, '+996700900007', 'Талант', 'Осмонов'),
    (Roles.DRIVER, '+996700900008', 'Эрмек', 'Турдубаев'),
    (Roles.FINANCE, '+996700900006', 'Демо', 'Финансист'),
    (Roles.CLIENT, '+996700900777', 'Айбек', 'Жумаев'),
    (Roles.CLIENT, '+996700900778', 'Гүлназ', 'Ибраева'),
]

CITIES = [
    ('Бишкек', 'BIS', Decimal('42.874621'), Decimal('74.569762')),
    ('Кара-Балта', 'KBL', Decimal('42.816700'), Decimal('73.850000')),
    ('Токтогул', 'TKT', Decimal('41.874700'), Decimal('72.938600')),
    ('Джалал-Абад', 'JAL', Decimal('40.933393'), Decimal('72.999672')),
    ('Ош', 'OSH', Decimal('40.514202'), Decimal('72.812204')),
    ('Каракол', 'KAR', Decimal('42.490527'), Decimal('78.393604')),
]

# Филиалы только в городах назначения; Кара-Балта и Токтогул — транзитные точки
BRANCH_CITIES = ('BIS', 'OSH', 'JAL', 'KAR')

# Филиал кладовщика: по нему приложение показывает рейсы склада
WAREHOUSE_BRANCHES = {'+996700900004': 'BIS', '+996700900009': 'OSH'}

# Точки маршрута Бишкек — Ош по порядку
ROUTE_BIS_OSH = ['BIS', 'KBL', 'TKT', 'JAL', 'OSH']

# По машине на каждый одновременно активный рейс (иначе VehicleBusyException)
VEHICLE_PLATES = ['01KG777AAA', '01KG777BBB', '01KG777CCC']
DRIVER_PHONES = ['+996700900005', '+996700900007', '+996700900008']

# Маркер демо-сценариев: по нему повторный запуск понимает, что всё уже создано
SCENARIO_MARK = 'Демо-сценарий'

# Заказ клиента доводится до оплаты этой цепочкой (актор — суперадмин)
PAID_CHAIN = (
    OrderStatus.WAITING_CONFIRMATION,
    OrderStatus.CONFIRMED,
    OrderStatus.WAITING_PAYMENT,
    OrderStatus.PAID,
)


def _box(title: str, weight: str, **extra) -> dict:
    return {
        'title': title,
        'weight': Decimal(weight),
        'length': 40,
        'width': 30,
        'height': 30,
        'declared_price': Decimal('5000'),
        **extra,
    }


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
            self._seed_employee_branches(branches)
            routes = self._seed_routes(actor, cities, branches)
            self._seed_tariffs(actor, cities)
            services = self._seed_services(actor)
            self._seed_warehouses(actor, branches)
            self._seed_fleet(actor, branches)
            self._seed_scenarios(actor, branches, services, routes)
        self._print_summary()
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
        for code in BRANCH_CITIES:
            city = cities[code]
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

    def _seed_employee_branches(self, branches) -> None:
        """Кладовщику нужен филиал: по нему приложение показывает рейсы склада."""
        for phone, city_code in WAREHOUSE_BRANCHES.items():
            profile = EmployeeProfile.objects.filter(user__phone=phone).first()
            if profile is not None and profile.branch_id is None:
                profile.branch = branches[city_code]
                profile.save(update_fields=['branch', 'updated_at'])
                self.stdout.write(f'  warehouse {phone} → филиал {branches[city_code].name}')

    def _seed_routes(self, actor, cities, branches) -> dict[str, Route]:
        """Маршруты с точками: по ним водитель отмечает пройденные города."""
        routes = {}
        for code, name, city_codes in (
            ('BIS-OSH', 'Бишкек — Ош', ROUTE_BIS_OSH),
            ('OSH-BIS', 'Ош — Бишкек', list(reversed(ROUTE_BIS_OSH))),
        ):
            route, _ = Route.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'start_branch': branches[city_codes[0]],
                    'end_branch': branches[city_codes[-1]],
                    'estimated_distance': Decimal('672.0'),
                    'estimated_duration': 720,
                    'created_by': actor,
                },
            )
            for sequence, city_code in enumerate(city_codes, start=1):
                city = cities[city_code]
                RoutePoint.objects.get_or_create(
                    route=route,
                    sequence=sequence,
                    defaults={
                        'city': city,
                        'latitude': city.latitude,
                        'longitude': city.longitude,
                        'created_by': actor,
                    },
                )
            routes[code] = route
        self.stdout.write(f'  routes: {len(routes)} (по {len(ROUTE_BIS_OSH)} точек)')
        return routes

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
        for plate, phone in zip(VEHICLE_PLATES, DRIVER_PHONES, strict=True):
            driver = User.objects.filter(role=Roles.DRIVER, phone=phone).first()
            vehicle, _ = Vehicle.objects.get_or_create(
                plate_number=plate,
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
                DriverProfile.objects.filter(user=driver, assigned_vehicle__isnull=True).update(
                    assigned_vehicle=vehicle
                )
        self.stdout.write(f'  fleet: 1 тип ТС, {len(VEHICLE_PLATES)} автомобиля (по одному на водителя)')

    # -------------------------------------------------------------- scenarios
    def _seed_scenarios(self, actor, branches, services, routes) -> None:
        """Заказы и рейсы во всех статусах, которые проверяет приложение.

        waiting_receive  — склад Бишкека принимает груз от клиента
        in_warehouse     — лежит в ячейке склада
        waiting_shipment — в рейсе READY, ждёт погрузки
        in_transit       — едет, у рейса две отметки точек
        arrived          — рейс прибыл в Ош, склад Оша разгружает
        ready_for_pickup — рейс завершён, склад Оша выдаёт получателю
        draft, damaged   — крайние состояния шкалы
        """
        if Order.objects.filter(comment__startswith=SCENARIO_MARK).exists():
            self.stdout.write('  scenarios: уже есть, пропуск')
            return

        client = User.objects.get(phone='+996700900777')
        client2 = User.objects.get(phone='+996700900778')
        drivers = [User.objects.get(phone=phone) for phone in DRIVER_PHONES]
        vehicles = [Vehicle.objects.get(plate_number=plate) for plate in VEHICLE_PLATES]
        cells = list(WarehouseCell.objects.filter(zone__warehouse__code='WH-BIS').order_by('code'))
        route = routes['BIS-OSH']
        ctx = {'actor': actor, 'branches': branches, 'services': services, 'cells': cells}

        # Порядок важен: завершённый рейс освобождает машину и водителя
        # для следующего, поэтому completed и arrived идут на одной паре.
        pickup = self._order(ctx, client, 'выдача', [_box('Ящик №1', '22.0'), _box('Ящик №2', '21.5')])
        self._to_warehouse(ctx, pickup, ready_for_shipment=True)
        self._make_trip(ctx, route, drivers[2], vehicles[2], [pickup], ShipmentStatus.COMPLETED)

        arrived = self._order(ctx, client2, 'прибыл', [_box('Сухофрукты, мешок', '40.0')])
        self._to_warehouse(ctx, arrived, ready_for_shipment=True)
        self._make_trip(ctx, route, drivers[2], vehicles[2], [arrived], ShipmentStatus.ARRIVED)

        transit = self._order(
            ctx, client, 'в пути', [_box('Телевизор 55"', '18.4', fragile=True), _box('Кронштейн', '3.2')]
        )
        self._to_warehouse(ctx, transit, ready_for_shipment=True)
        self._make_trip(ctx, route, drivers[0], vehicles[0], [transit], ShipmentStatus.IN_TRANSIT, marks=2)

        waiting_trip = self._order(ctx, client2, 'на погрузку', [_box('Мешок с текстилем', '8.0')])
        self._to_warehouse(ctx, waiting_trip, ready_for_shipment=True)
        self._make_trip(ctx, route, drivers[1], vehicles[1], [waiting_trip], ShipmentStatus.READY)

        stored = self._order(ctx, client, 'склад', [_box('Коробка с запчастями', '12.5')])
        self._to_warehouse(ctx, stored)

        waiting = self._order(ctx, client, 'приём', [_box('Коробка с посудой', '6.3', fragile=True)])
        self._advance(ctx, waiting, (*PAID_CHAIN, OrderStatus.WAITING_RECEIVE))

        damaged = self._order(ctx, client, 'повреждён', [_box('Сервиз', '9.1', fragile=True)])
        self._to_warehouse(ctx, damaged)
        self._advance(ctx, damaged, (OrderStatus.DAMAGED,))

        self._order(ctx, client, 'черновик', [_box('Сумка с одеждой', '4.2')])
        self.stdout.write('  scenarios: 8 заказов, 4 рейса (ready, in_transit, arrived, completed)')

    @staticmethod
    def _order(ctx, client, title: str, packages: list[dict]) -> Order:
        """Заказ Бишкек → Ош с QR на каждом месте (без QR груз не отсканировать)."""
        actor, branches = ctx['actor'], ctx['branches']
        order = OrderService.create(
            actor=actor,
            client=client,
            sender_name=client.full_name or 'Демо Отправитель',
            sender_phone=client.phone,
            sender_address='Бишкек, ул. Киевская, 95',
            receiver_name=f'Получатель ({title})',
            receiver_phone='+996700900888',
            receiver_address='Ош, ул. Масалиева, 32',
            from_branch=branches['BIS'],
            to_branch=branches['OSH'],
            payment_type=PaymentType.CASH,
            delivery_type=DeliveryType.BRANCH_PICKUP,
            comment=f'{SCENARIO_MARK}: {title} (seed_demo)',
            packages=packages,
            services=ctx['services'][:1],
        )
        for package in order.packages.all():
            PackageService.generate_qr(actor=actor, package=package)
        return order

    @staticmethod
    def _advance(ctx, order: Order, statuses) -> Order:
        # Сервис меняет заблокированную копию — держим переданный объект в актуальном
        # статусе: грузы ссылаются на него же (package.order) при синхронизации склада.
        for to_status in statuses:
            order.refresh_from_db()
            OrderTransitionService.change(order=order, to_status=to_status, actor=ctx['actor'])
        order.refresh_from_db()
        return order

    def _to_warehouse(self, ctx, order: Order, *, ready_for_shipment: bool = False) -> None:
        """Приём → проверка → размещение в ячейку склада Бишкека.

        Приём и проверку проводим переходами (реальный приём требует фото),
        размещение — складским сервисом: он ведёт заполненность ячеек и сам
        переводит заказ в IN_WAREHOUSE.
        """
        actor, cells = ctx['actor'], ctx['cells']
        self._advance(ctx, order, (*PAID_CHAIN, OrderStatus.WAITING_RECEIVE, OrderStatus.RECEIVED))
        for package in order.packages.all():
            for to_status in (PackageStatus.RECEIVED, PackageStatus.CHECKED):
                PackageTransitionService.change(package=package, to_status=to_status, actor=actor)
            cell = cells[Package.objects.filter(current_cell__isnull=False).count() % len(cells)]
            WarehouseOperationsService.store(actor=actor, package=package, cell=cell, reason='seed_demo')
        if ready_for_shipment:
            self._advance(ctx, order, (OrderStatus.WAITING_SHIPMENT,))

    @staticmethod
    def _make_trip(ctx, route, driver, vehicle, orders, target: str, *, marks: int | None = None) -> Shipment:
        """Рейс Бишкек → Ош, доведённый до target реальными операциями.

        marks — сколько первых точек маршрута отметить (по умолчанию после
        прибытия отмечены все, в пути — ни одной).
        """
        actor, branches = ctx['actor'], ctx['branches']
        shipment = ShipmentService.create(
            actor=actor,
            departure_branch=branches['BIS'],
            arrival_branch=branches['OSH'],
            route=route,
            vehicle=vehicle,
            driver=driver,
            planned_departure=timezone.now() + timedelta(hours=3),
        )
        for order in orders:
            ShipmentService.add_order(actor=actor, shipment=shipment, order=order)

        def transition(to_status):
            return ShipmentTransitionService.change(shipment=shipment, to_status=to_status, actor=actor)

        shipment = transition(ShipmentStatus.PLANNED)
        shipment = transition(ShipmentStatus.READY)
        if target == ShipmentStatus.READY:
            return shipment

        shipment = transition(ShipmentStatus.LOADING)
        for item in shipment.items.select_related('package'):
            ShipmentService.load_package(actor=actor, shipment=shipment, qr_code=item.package.qr_code)
        shipment = ShipmentService.finish_loading(actor=actor, shipment=shipment)
        shipment = ShipmentService.start(actor=driver, shipment=Shipment.objects.get(id=shipment.id))

        points = list(route.points.order_by('sequence'))
        count = marks if marks is not None else len(points)
        if target == ShipmentStatus.IN_TRANSIT:
            Command._mark_checkpoints(shipment, driver, points[:count])
            return shipment

        Command._mark_checkpoints(shipment, driver, points[:count])
        shipment = ShipmentService.arrive(actor=driver, shipment=shipment)
        if target == ShipmentStatus.ARRIVED:
            return shipment

        shipment = transition(ShipmentStatus.UNLOADING)
        for item in shipment.items.select_related('package'):
            ShipmentService.unload_package(actor=actor, shipment=shipment, qr_code=item.package.qr_code)
        return ShipmentService.finish(actor=actor, shipment=shipment)

    @staticmethod
    def _mark_checkpoints(shipment, driver, points) -> None:
        """Пройденные точки маршрута — клиент видит их в трекинге заказа."""
        now = timezone.now()
        for index, point in enumerate(points):
            ShipmentCheckpointService.mark(
                actor=driver,
                shipment=shipment,
                client_id=uuid.uuid4(),
                route_point_id=point.id,
                reached_at=now - timedelta(hours=2 * (len(points) - index)),
                comment='Заправка, 15 минут' if index == 1 else '',
            )

    # ---------------------------------------------------------------- summary
    def _print_summary(self) -> None:
        """Учётки, QR-коды и рейсы: без них приложение нечем проверить."""
        self.stdout.write(self.style.SUCCESS(f'\n=== Учётки (пароль {DEMO_PASSWORD}) ==='))
        for role, phone, first, last in DEMO_USERS:
            self.stdout.write(f'  {role:10s} {phone}  {last} {first}')

        self.stdout.write(self.style.SUCCESS('\n=== QR-коды грузов (для сканера) ==='))
        packages = (
            Package.objects.select_related('order')
            .filter(order__comment__startswith=SCENARIO_MARK)
            .exclude(qr_code='')
            .order_by('created_at')
        )
        for package in packages:
            self.stdout.write(
                f'  {package.qr_code}  {package.order.order_number}  '
                f'{package.status:16s} {package.title}'
            )

        self.stdout.write(self.style.SUCCESS('\n=== Рейсы ==='))
        shipments = Shipment.objects.select_related('driver', 'route').filter(
            driver__phone__in=DRIVER_PHONES
        )
        for shipment in shipments.order_by('created_at'):
            self.stdout.write(
                f'  {shipment.shipment_number}  {shipment.status:12s} '
                f'маршрут={shipment.route.code if shipment.route else "—"}  '
                f'водитель={shipment.driver.phone}  отметок={shipment.checkpoints.count()}'
            )

    # ------------------------------------------------------------------- wipe
    def _wipe(self) -> None:
        phones = [phone for _, phone, _, _ in DEMO_USERS]
        Shipment.all_objects.filter(created_by__phone__in=phones).hard_delete()
        User.all_objects.filter(phone__in=phones).hard_delete()
        self.stdout.write(self.style.WARNING('Демо-пользователи и их рейсы удалены (справочники оставлены).'))
        self.stdout.write('Заказы/грузы/справочники удаляйте вручную при необходимости (PROTECT-связи).')
