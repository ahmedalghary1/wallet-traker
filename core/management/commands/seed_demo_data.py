import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import BankAccount, SystemSettings, Transaction, Wallet


DEMO_WALLETS = [
    {
        "name": "محفظة المبيعات - الفرع الرئيسي",
        "wallet_type": Wallet.VODAFONE,
        "phone_number": "01023874591",
        "opening_balance": Decimal("8500.00"),
    },
    {
        "name": "محفظة خدمة العملاء",
        "wallet_type": Wallet.ORANGE,
        "phone_number": "01277418526",
        "opening_balance": Decimal("6200.00"),
    },
    {
        "name": "محفظة التحويلات السريعة",
        "wallet_type": Wallet.INSTAPAY,
        "phone_number": "01553690184",
        "opening_balance": Decimal("12500.00"),
    },
    {
        "name": "محفظة المصروفات التشغيلية",
        "wallet_type": Wallet.OTHER,
        "phone_number": "01149276035",
        "opening_balance": Decimal("4800.00"),
    },
]

DEMO_BANKS = [
    {
        "bank_name": "البنك الأهلي المصري",
        "account_name": "الحساب الرئيسي للشركة",
        "account_number": "NBE-1045287391",
        "notes": "حساب استقبال التحويلات اليومية",
    },
    {
        "bank_name": "بنك مصر",
        "account_name": "حساب المصروفات",
        "account_number": "BM-2093817465",
        "notes": "يستخدم لتسوية مصروفات التشغيل",
    },
    {
        "bank_name": "CIB",
        "account_name": "حساب التحصيل الإلكتروني",
        "account_number": "CIB-7736402819",
        "notes": "حساب مخصص لتجميع إيرادات المحافظ",
    },
    {
        "bank_name": "QNB الأهلي",
        "account_name": "حساب الاحتياطي",
        "account_number": "QNB-3849201756",
        "notes": "تحويلات احتياطية عند زيادة الرصيد",
    },
]

CUSTOMER_FIRST_NAMES = [
    "أحمد",
    "محمد",
    "محمود",
    "مصطفى",
    "كريم",
    "خالد",
    "يوسف",
    "عمر",
    "منة",
    "سارة",
    "نور",
    "إسراء",
    "هدير",
    "مريم",
    "آية",
    "دينا",
]

CUSTOMER_LAST_NAMES = [
    "عبد الرحمن",
    "حسن",
    "إبراهيم",
    "السيد",
    "علي",
    "جمال",
    "فؤاد",
    "مراد",
    "النجار",
    "منصور",
    "الشربيني",
    "عبد الله",
]

PAYMENT_NOTES = [
    "تحصيل طلبات اليوم",
    "دفع فاتورة خدمة",
    "تحويل عميل من الفرع",
    "تسوية مبيعات أونلاين",
    "دفعة مقدمة من عميل",
    "تحصيل اشتراك شهري",
]

TRANSFER_NOTES = [
    "تسوية رصيد نهاية اليوم",
    "تحويل فائض الرصيد إلى البنك",
    "تجميع أرصدة المحافظ",
    "تغذية حساب المصروفات",
]


class Command(BaseCommand):
    help = "Seed realistic demo wallets, bank accounts, and transactions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--transactions",
            type=int,
            default=120,
            help="Number of demo transactions to create or update.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=20260505,
            help="Stable random seed used to generate repeatable demo data.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Spread demo transactions over the last N days.",
        )
        parser.add_argument(
            "--reset-demo",
            action="store_true",
            help="Delete existing demo transactions with DEMO- references before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        transaction_count = max(options["transactions"], 0)
        day_count = max(options["days"], 1)
        rng = random.Random(options["seed"])

        if options["reset_demo"]:
            deleted_count, _ = Transaction.objects.filter(
                reference_number__startswith="DEMO-"
            ).delete()
            self.stdout.write(f"Deleted {deleted_count} old demo transactions.")

        settings_obj = SystemSettings.load()
        settings_obj.company_name = "شركة الوفاق للخدمات المالية"
        settings_obj.default_currency = "جنيه"
        settings_obj.notes = "بيانات تجريبية لأغراض العرض والاختبار."
        settings_obj.save()

        wallets = self._create_wallets()
        banks = self._create_banks()
        created_count = 0
        updated_count = 0

        for index in range(1, transaction_count + 1):
            defaults = self._build_transaction_defaults(index, wallets, banks, rng, day_count)
            _, created = Transaction.objects.update_or_create(
                reference_number=f"DEMO-{index:05d}",
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready: {len(wallets)} wallets, "
                f"{len(banks)} bank accounts, {created_count} new transactions, "
                f"{updated_count} updated transactions."
            )
        )

    def _create_wallets(self):
        wallets = []
        for item in DEMO_WALLETS:
            wallet, _ = Wallet.objects.update_or_create(
                name=item["name"],
                defaults={
                    "wallet_type": item["wallet_type"],
                    "phone_number": item["phone_number"],
                    "opening_balance": item["opening_balance"],
                    "is_active": True,
                },
            )
            wallets.append(wallet)
        return wallets

    def _create_banks(self):
        banks = []
        for item in DEMO_BANKS:
            bank, _ = BankAccount.objects.update_or_create(
                account_number=item["account_number"],
                defaults={
                    "bank_name": item["bank_name"],
                    "account_name": item["account_name"],
                    "notes": item["notes"],
                    "is_active": True,
                },
            )
            banks.append(bank)
        return banks

    def _build_transaction_defaults(self, index, wallets, banks, rng, day_count):
        transaction_date = self._random_date(rng, day_count)
        is_transfer_to_bank = rng.random() < 0.24
        wallet = rng.choice(wallets)

        if is_transfer_to_bank:
            amount = self._money(rng, 1000, 8500, step=50)
            fee = self._money(rng, 0, 35, step=5)
            return {
                "transaction_type": Transaction.WALLET_TO_BANK,
                "wallet": wallet,
                "bank_account": rng.choice(banks),
                "customer_name": "",
                "customer_phone": "",
                "amount": amount,
                "fee": fee,
                "transaction_date": transaction_date,
                "notes": rng.choice(TRANSFER_NOTES),
                "created_by": None,
            }

        amount = self._money(rng, 100, 3200, step=25)
        fee = self._fee_for_amount(amount, rng)
        return {
            "transaction_type": Transaction.CUSTOMER_PAYMENT,
            "wallet": wallet,
            "bank_account": None,
            "customer_name": self._customer_name(rng),
            "customer_phone": self._egyptian_mobile(rng, index),
            "amount": amount,
            "fee": fee,
            "transaction_date": transaction_date,
            "notes": rng.choice(PAYMENT_NOTES),
            "created_by": None,
        }

    def _random_date(self, rng, day_count):
        days_back = rng.randint(0, day_count - 1)
        hour = rng.randint(9, 22)
        minute = rng.choice([0, 5, 10, 15, 20, 30, 35, 40, 45, 50, 55])
        return timezone.localtime().replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        ) - timedelta(days=days_back)

    def _money(self, rng, minimum, maximum, step):
        units = rng.randint(minimum // step, maximum // step)
        return Decimal(units * step).quantize(Decimal("0.01"))

    def _fee_for_amount(self, amount, rng):
        percentage_fee = (amount * Decimal("0.01")).quantize(Decimal("0.01"))
        minimum_fee = Decimal(rng.choice([2, 3, 5, 7, 10]))
        return max(percentage_fee, minimum_fee)

    def _customer_name(self, rng):
        return f"{rng.choice(CUSTOMER_FIRST_NAMES)} {rng.choice(CUSTOMER_LAST_NAMES)}"

    def _egyptian_mobile(self, rng, index):
        prefix = rng.choice(["010", "011", "012", "015"])
        return f"{prefix}{(23500000 + index * 137 + rng.randint(0, 9999)) % 100000000:08d}"
