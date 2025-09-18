from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone



class CustomUser(AbstractUser):
    USER_TYPES = [
        ('contractor', 'Contractor'),
        ('worker', 'Worker'),
        ('supplier', 'Supplier'),
    ]

    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    hourly_wage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # New ForeignKey to Company
    company = models.ForeignKey('Company', null=True, blank=True, on_delete=models.SET_NULL)

    last_login = models.DateTimeField(blank=True, null=True)

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True)  # Manually entered 5-digit code
    contractor = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_company',
        limit_choices_to={'user_type': 'contractor'}
    )
    workers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='companies',
        limit_choices_to={'user_type': 'worker'},
        blank=True
    )

    def __str__(self):
        return f"{self.name} (Code: {self.code})"


class Attendance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    total_hours = models.FloatField(default=0)
    flag = models.IntegerField(default=0)
    clock_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class PasswordResetCode(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at).seconds < 600  # valid 10 mins

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField(blank=True)
    file = models.FileField(upload_to='messages/files/', blank=True, null=True)
    image = models.ImageField(upload_to='messages/images/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class MonthlyReport(models.Model):
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    total_days = models.IntegerField(default=0)
    total_hours = models.FloatField(default=0)
    payroll_file = models.FileField(upload_to='payrolls/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('worker', 'month', 'year')

    def __str__(self):
        return f"{self.worker.username} – {self.month}/{self.year}"

    @property
    def salary(self):
        wage = self.worker.hourly_wage or Decimal("0.00")
        hours = Decimal(str(self.total_hours))
        return (wage * hours).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class Project(models.Model):
    PROJECT_TYPES = [
        ('drywall', 'Drywall'),
        ('aluminum', 'Aluminum'),
    ]

    project_number = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=255)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    blueprints = models.FileField(upload_to='blueprints/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    contractor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        limit_choices_to={'user_type': 'contractor'}
    )

    workers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_projects',
        limit_choices_to={'user_type': 'worker'}
    )

    def __str__(self):
        return f"Project {self.project_number}"



class Room(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rooms')
    blueprint = models.FileField(upload_to='room_blueprints/', blank=True, null=True)

    def __str__(self):
        return f"Room {self.name} in Project {self.project.project_number}"



class Glass(models.Model):
    GLASS_TYPES = [
        ('transparent', 'Transparent'),
        ('anti_sun', 'Anti-Sun'),
        ('shadowed', 'Shadowed'),
        ('בודדי', 'בודדי'),
    ]

    glass_type = models.CharField(max_length=20, choices=GLASS_TYPES)
    height = models.DecimalField(max_digits=7, decimal_places=2)
    width = models.DecimalField(max_digits=7, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.price is None:
            try:
                from .models import GlassPrice  # import inside to avoid circular import
                contractor = kwargs.pop('contractor', None)

                if contractor:
                    price_entry = GlassPrice.objects.get(
                        contractor=contractor,
                        glass_type=self.glass_type
                    )
                    area_m2 = Decimal(self.height) * Decimal(self.width) / Decimal('10000')
                    self.price = round(area_m2 * price_entry.price_per_m2, 2)

            except (GlassPrice.DoesNotExist, ObjectDoesNotExist):
                self.price = Decimal('0.00')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.glass_type} Glass ({self.height}x{self.width})"

class Window(models.Model):
    WINDOW_TYPES = [
        ('sliding', 'Sliding'),
        ('multi_bolt', 'Multi-Bolt'),
    ]

    SLIDING_ALUMINUM_TYPES = [
        ('1700', '1700'), ('7000', '7000'), ('7300', '7300'), ('9000', '9000'), ('9200', '9200'),
    ]

    MULTI_BOLT_ALUMINUM_TYPES = [
        ('4400', '4400'), ('4300', '4300'), ('4500', '4500'), ('9400', '9400'),
    ]

    window_number = models.CharField(max_length=50, unique=True)
    window_type = models.CharField(max_length=10, choices=WINDOW_TYPES)
    number_of_sashs = models.IntegerField()
    aluminum_type = models.CharField(max_length=10)
    room = models.ForeignKey('Room', on_delete=models.SET_NULL, related_name='windows', null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='windows')

    def __str__(self):
        return f"{self.window_type.capitalize()} Window {self.window_number}"

class WindowFrame(models.Model):
    window = models.OneToOneField('Window', on_delete=models.CASCADE, related_name='window_frame')
    side = models.DecimalField(max_digits=7, decimal_places=2)
    top = models.DecimalField(max_digits=7, decimal_places=2)
    bottom = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return f"Frame for Window {self.window.window_number}"

class WindowSash(models.Model):
    window = models.ForeignKey('Window', on_delete=models.CASCADE, related_name='window_sashes')
    side = models.DecimalField(max_digits=7, decimal_places=2)
    top = models.DecimalField(max_digits=7, decimal_places=2)
    bottom = models.DecimalField(max_digits=7, decimal_places=2)
    glass = models.ForeignKey(Glass, on_delete=models.CASCADE, related_name='window_sashes')

    def __str__(self):
        return f"Sash for Window {self.window.window_number}"

class Door(models.Model):
    DOOR_TYPES = [
        ('sliding', 'Sliding'),
        ('multi_bolt', 'Multi-Bolt'),
    ]

    SLIDING_ALUMINUM_TYPES = [
        ('2200', '2200'), ('9400', '9400'), ('9200', '9200'), ('7300', '7300'),
    ]

    MULTI_BOLT_ALUMINUM_TYPES = [
        ('2000', '2000'), ('4500', '4500'), ('4400', '4400'),
    ]

    door_number = models.CharField(max_length=50, unique=True)
    door_type = models.CharField(max_length=10, choices=DOOR_TYPES)
    number_of_sashs = models.IntegerField()
    aluminum_type = models.CharField(max_length=10)
    room = models.ForeignKey('Room', on_delete=models.SET_NULL, related_name='doors', null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='doors')

    def __str__(self):
        return f"{self.door_type.capitalize()} Door {self.door_number}"

class DoorFrame(models.Model):
    door = models.OneToOneField('Door', on_delete=models.CASCADE, related_name='door_frame')
    side = models.DecimalField(max_digits=7, decimal_places=2)
    top = models.DecimalField(max_digits=7, decimal_places=2)
    bottom = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Frame for Door {self.door.door_number}"

class DoorSash(models.Model):
    door = models.ForeignKey('Door', on_delete=models.CASCADE, related_name='door_sashes')
    side = models.DecimalField(max_digits=7, decimal_places=2)
    top = models.DecimalField(max_digits=7, decimal_places=2)
    bottom = models.DecimalField(max_digits=7, decimal_places=2)
    glass = models.ForeignKey(Glass, on_delete=models.CASCADE, related_name='door_sashes')

    def __str__(self):
        return f"Sash for Door {self.door.door_number}"


class AluminumPrice(models.Model):
    contractor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'contractor'})
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    aluminum_type = models.CharField(max_length=10)  # 1700, 9200, etc.
    price_per_m2 = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('contractor', 'aluminum_type')


class GlassPrice(models.Model):
    contractor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'contractor'})
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    glass_type = models.CharField(max_length=20, choices=Glass.GLASS_TYPES)
    price_per_m2 = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('contractor', 'glass_type')

class DrywallBoardPrice(models.Model):
    contractor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'contractor'})
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    color = models.CharField(max_length=10)  # green, blue, etc.
    size = models.CharField(max_length=20)  # e.g., 200x120
    price_per_board = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('contractor', 'color', 'size')

class MetalProfilePrice(models.Model):
    contractor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'contractor'})
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    profile_type = models.CharField(max_length=10)  # stud or track
    thickness = models.CharField(max_length=10)  # e.g., 37, 50, 70, F47
    price_per_meter = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('contractor', 'profile_type', 'thickness')



class Wall(models.Model):
    DRYWALL_TYPES = [
        ('white', 'White'),
        ('pink', 'Pink (Fire-Resistant)'),
        ('green', 'Green (Moisture-Resistant)'),
        ('blue', 'Blue (Acoustic)'),
    ]

    STUD_THICKNESSES = [
        ('37', '37mm'),
        ('50', '50mm'),
        ('70', '70mm'),
        ('100', '100mm'),
        ('f47', 'F47'),
    ]

    BOARD_SIZES = [
        (2.0, "2000 mm (2.0 m)"),
        (2.6, "2600 mm (2.6 m)"),
        (3.0, "3000 mm (3.0 m)"),
    ]

    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='walls')
    width = models.DecimalField(max_digits=6, decimal_places=2)   # meters
    height = models.DecimalField(max_digits=6, decimal_places=2)
    drywall_type = models.CharField(max_length=10, choices=DRYWALL_TYPES)
    stud_thickness = models.CharField(max_length=10, choices=STUD_THICKNESSES)
    number_of_layers = models.PositiveSmallIntegerField(default=1)  # 1 or 2 max
    double_sided = models.BooleanField(default=False)
    board_length = models.DecimalField(max_digits=3, decimal_places=1, choices=BOARD_SIZES, default=2.6)

    def __str__(self):
        return f"Wall ({self.width}×{self.height}) in Room {self.room.name}"

    @property
    def area(self):
        return self.width * self.height


class Ceiling(models.Model):
    DRYWALL_TYPES = [
        ('white', 'White'),
        ('pink', 'Pink (Fire-Resistant)'),
        ('green', 'Green (Moisture-Resistant)'),
        ('blue', 'Blue (Acoustic)'),
    ]

    STUD_THICKNESSES = [
        ('37', '37mm'),
        ('50', '50mm'),
        ('70', '70mm'),
        ('100', '100mm'),
        ('f47', 'F47'),
    ]

    BOARD_SIZES = [
        (2.0, "2000 mm (2.0 m)"),
        (2.6, "2600 mm (2.6 m)"),
        (3.0, "3000 mm (3.0 m)"),
    ]

    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='ceilings')
    area = models.DecimalField(max_digits=8, decimal_places=2)   # square meters
    drywall_type = models.CharField(max_length=10, choices=DRYWALL_TYPES)
    stud_thickness = models.CharField(max_length=10, choices=STUD_THICKNESSES)
    board_length = models.DecimalField(max_digits=3, decimal_places=1, choices=BOARD_SIZES, default=2.6)

    def __str__(self):
        return f"Ceiling ({self.area} m²) in Room {self.room.name}"


class DrywallMaterial(models.Model):
    project = models.OneToOneField('Project', on_delete=models.CASCADE, related_name='drywall_material')

    # Totals
    total_board_count = models.PositiveIntegerField(default=0)
    total_stud_length = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # ניצב
    total_track_length = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # מסלול

    last_calculated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Drywall Materials for Project {self.project.project_number}"

class AluminumMaterial(models.Model):
    project = models.OneToOneField('Project', on_delete=models.CASCADE, related_name='aluminum_material')

    # Frame totals (meters)
    frame_top_bottom_length = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    frame_side_length = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Sash totals (meters)
    sash_side_length = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    sash_top_bottom_length = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    sash_handle_side_length = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    last_calculated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Aluminum Material Summary for Project {self.project.project_number}"

class AluminumProfile(models.Model):
    PROFILE_TYPE_CHOICES = [
        ('1700', '1700'), ('7000', '7000'), ('7300', '7300'),
        ('9000', '9000'), ('9200', '9200'), ('2200', '2200'),
        ('9400', '9400'), ('2000', '2000'), ('4500', '4500'),
        ('4400', '4400'), ('4300', '4300'),
    ]

    USE_CHOICES = [
        ('window', 'Window'),
        ('door', 'Door'),
    ]

    type = models.CharField(max_length=10, choices=PROFILE_TYPE_CHOICES)
    use = models.CharField(max_length=10, choices=USE_CHOICES)
    color = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.type} ({self.use}) - {self.color}"


class ProfileSet(models.Model):
    SET_KIND_CHOICES = [
        ('frame', 'Frame'),
        ('sash', 'Sash'),
    ]

    aluminum_profile = models.ForeignKey(
        AluminumProfile,
        on_delete=models.CASCADE,
        related_name='sets'
    )
    kind = models.CharField(max_length=10, choices=SET_KIND_CHOICES)
    name = models.CharField(max_length=100)
    code_string = models.CharField(max_length=50)
    set_code = models.PositiveIntegerField(unique=True)
    weight_per_meter = models.DecimalField(max_digits=6, decimal_places=3)
    price_per_kilo = models.DecimalField(max_digits=8, decimal_places=2)

    supplier = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'supplier'}
    )
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kind.capitalize()} Set {self.set_code} - {self.name} - ₪{self.price_per_kilo}/kg"


class Screw(models.Model):
    LENGTH_CHOICES = [
        (2.5, '2.5 cm'), (3.5, '3.5 cm'), (4.5, '4.5 cm'),
        (5.0, '5 cm'), (7.0, '7 cm'), (10.0, '10 cm'),
    ]

    TYPE_CHOICES = [
        ('drywall', 'Drywall'),
        ('dowel', 'Dowel'),
        ('screw', 'Regular Screw'),
        ('stainless', 'Stainless Steel'),
    ]

    COUNT_CHOICES = [
        (100, '100'), (500, '500'), (1000, '1000'), (10000, '10000'),
    ]

    screw_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    length_cm = models.DecimalField(max_digits=4, decimal_places=1, choices=LENGTH_CHOICES)
    count_per_box = models.PositiveIntegerField(choices=COUNT_CHOICES)
    price_per_100 = models.DecimalField(max_digits=8, decimal_places=2)

    supplier = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'supplier'}
    )
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.screw_type} {self.length_cm}cm - {self.count_per_box}pcs - ₪{self.price_per_100}/100"


class MetalProfile(models.Model):
    PROFILE_TYPE_CHOICES = [
        ('stud', 'Stud'),
        ('track', 'Track'),
    ]

    SIZE_CHOICES = [
        ('37', '37 mm'), ('50', '50 mm'),
        ('70', '70 mm'), ('100', '100 mm'), ('f47', 'F47'),
    ]

    profile_type = models.CharField(max_length=10, choices=PROFILE_TYPE_CHOICES)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    length_meters = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
    quantity = models.PositiveIntegerField()
    price_per_piece = models.DecimalField(max_digits=8, decimal_places=2)

    supplier = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'supplier'}
    )
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile_type} {self.size} - {self.quantity}pcs - ₪{self.price_per_piece}/piece"


class DrywallBoard(models.Model):
    COLOR_CHOICES = [
        ('pink', 'Pink'), ('green', 'Green'),
        ('white', 'White'), ('blue', 'Blue'),
    ]

    SIZE_CHOICES = [
        ('200x120', '200 x 120 cm'),
        ('260x120', '260 x 120 cm'),
        ('300x120', '300 x 120 cm'),
    ]

    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES)
    thickness_mm = models.PositiveIntegerField(default=12)
    quantity = models.PositiveIntegerField()
    price_per_board = models.DecimalField(max_digits=8, decimal_places=2)

    supplier = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'supplier'}
    )
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.color} {self.size} - {self.quantity}pcs - ₪{self.price_per_board}/board"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    order_number = models.CharField(max_length=20, unique=True,blank=True)
    item_description = models.TextField(blank=True, null=True)

    contractor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'contractor'}
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    supplier = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='orders_received',
        limit_choices_to={'user_type': 'supplier'}
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)  # NEW: Supplier must fill before approval
    contractor_approved = models.BooleanField(default=False)  # NEW: Contractor must approve before sending

    def __str__(self):
        return f"Order {self.order_number} from {self.contractor.username}"

    def total_before_tax(self):
        return sum(item.total_price() for item in self.items.all())

    def total_after_tax(self):
        return self.total_before_tax() * Decimal('1.18')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.item_name} x {self.quantity} for Order {self.order.order_number}"



def generate_monthly_reports_from_attendance(company_id):
    User = get_user_model()
    workers = User.objects.filter(user_type='worker', company_id=company_id)

    for worker in workers:
        attendances = Attendance.objects.filter(
            user=worker,
            clock_in__isnull=False,
            clock_out__isnull=False
        )

        # Group attendance records by (year, month)
        grouped = defaultdict(list)
        for att in attendances:
            key = (att.date.year, att.date.month)
            grouped[key].append(att)

        for (year, month), records in grouped.items():
            if MonthlyReport.objects.filter(worker=worker, year=year, month=month).exists():
                continue

            total_days = len(records)
            total_hours = sum(att.total_hours for att in records)

            MonthlyReport.objects.create(
                worker=worker,
                year=year,
                month=month,
                total_days=total_days,
                total_hours=total_hours
            )

    print(f"✅ Reports created for company {company_id} where missing.")



