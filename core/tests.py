from decimal import Decimal
from io import StringIO
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from .models import BankAccount, SystemSettings, Transaction, Wallet


class WalletTrackerTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin", password="password", is_staff=True, is_superuser=True
        )
        self.wallet = Wallet.objects.create(
            name="محفظة رئيسية",
            wallet_type=Wallet.VODAFONE,
            phone_number="01000000000",
            opening_balance=Decimal("100.00"),
        )
        self.bank = BankAccount.objects.create(
            bank_name="بنك الشركة",
            account_name="حساب الشركة",
            account_number="123456",
        )

    def test_net_amount_and_wallet_balance_are_calculated(self):
        Transaction.objects.create(
            transaction_type=Transaction.CUSTOMER_PAYMENT,
            wallet=self.wallet,
            customer_name="عميل",
            amount=Decimal("500.00"),
            fee=Decimal("5.00"),
            reference_number="T-1",
            transaction_date=timezone.now(),
            created_by=self.admin,
        )
        transfer = Transaction.objects.create(
            transaction_type=Transaction.WALLET_TO_BANK,
            wallet=self.wallet,
            bank_account=self.bank,
            amount=Decimal("120.00"),
            fee=Decimal("2.00"),
            reference_number="T-2",
            transaction_date=timezone.now(),
            created_by=self.admin,
        )

        self.assertEqual(transfer.net_amount, Decimal("118.00"))
        self.assertEqual(self.wallet.current_balance(), Decimal("473.00"))

    def test_core_pages_and_export_excel_are_available_without_login(self):
        Transaction.objects.create(
            transaction_type=Transaction.CUSTOMER_PAYMENT,
            wallet=self.wallet,
            customer_name="عميل",
            amount=Decimal("250.00"),
            fee=Decimal("3.00"),
            reference_number="T-3",
            transaction_date=timezone.now(),
            created_by=self.admin,
        )

        for path in ["/", "/transactions/", "/transactions/add/", "/wallets/", "/banks/", "/reports/", "/settings/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

        self.assertRedirects(self.client.get("/login/"), "/")
        self.assertRedirects(self.client.post("/logout/"), "/")
        self.assertEqual(self.client.get("/admin/").status_code, 404)

        response = self.client.get(f"/reports/export-excel/?wallet={self.wallet.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response["Content-Type"].startswith(
                "application/vnd.openxmlformats-officedocument"
            )
        )

    def test_local_app_can_work_without_login(self):
        for path in ["/", "/transactions/", "/transactions/add/", "/wallets/", "/banks/", "/reports/", "/settings/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

        response = self.client.post(
            "/transactions/add/",
            {
                "transaction_type": Transaction.CUSTOMER_PAYMENT,
                "wallet": str(self.wallet.pk),
                "customer_name": "عميل محلي",
                "amount": "150.00",
                "fee": "5.00",
                "net_amount": "145.00",
                "reference_number": "LOCAL-1",
                "transaction_date": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertEqual(response.status_code, 302)
        transaction = Transaction.objects.get(reference_number="LOCAL-1")
        self.assertIsNone(transaction.created_by)
        self.assertEqual(transaction.net_amount, Decimal("145.00"))

    def test_seed_demo_data_command_creates_realistic_records(self):
        output = StringIO()

        call_command(
            "seed_demo_data",
            transactions=12,
            seed=123,
            stdout=output,
        )

        self.assertGreaterEqual(Wallet.objects.count(), 4)
        self.assertGreaterEqual(BankAccount.objects.count(), 4)
        self.assertEqual(
            Transaction.objects.filter(reference_number__startswith="DEMO-").count(),
            12,
        )
        self.assertIn("Demo data ready", output.getvalue())

    def test_reference_number_must_be_unique_when_provided(self):
        Transaction.objects.create(
            transaction_type=Transaction.CUSTOMER_PAYMENT,
            wallet=self.wallet,
            amount=Decimal("100.00"),
            fee=Decimal("0.00"),
            reference_number="DUP-1",
            transaction_date=timezone.now(),
            created_by=self.admin,
        )

        response = self.client.post(
            "/transactions/add/",
            {
                "transaction_type": Transaction.CUSTOMER_PAYMENT,
                "wallet": str(self.wallet.pk),
                "amount": "100.00",
                "fee": "0.00",
                "net_amount": "100.00",
                "reference_number": "DUP-1",
                "transaction_date": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "رقم العملية مستخدم من قبل.")


class BackupTests(TransactionTestCase):
    def test_backup_endpoint_creates_zip_archive(self):
        with TemporaryDirectory(dir=settings.BASE_DIR) as temp_dir:
            settings_obj = SystemSettings.load()
            settings_obj.backup_directory = temp_dir
            settings_obj.save()

            response = self.client.post("/backup/create/")

            self.assertEqual(response.status_code, 200)
            archive_path = response.json()["path"]
            with ZipFile(archive_path) as archive:
                self.assertIn("db.sqlite3", archive.namelist())
                self.assertIn("backup-manifest.json", archive.namelist())
