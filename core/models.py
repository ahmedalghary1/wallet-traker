from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q, Sum


IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        abstract = True


class Wallet(TimeStampedModel):
    VODAFONE = "vodafone_cash"
    ORANGE = "orange_cash"
    INSTAPAY = "instapay"
    OTHER = "other"

    WALLET_TYPES = [
        (VODAFONE, "Vodafone Cash"),
        (ORANGE, "Orange Cash"),
        (INSTAPAY, "InstaPay"),
        (OTHER, "أخرى"),
    ]

    name = models.CharField("اسم المحفظة", max_length=120)
    wallet_type = models.CharField("نوع المحفظة", max_length=40, choices=WALLET_TYPES)
    phone_number = models.CharField("رقم المحفظة", max_length=30)
    opening_balance = models.DecimalField(
        "الرصيد الافتتاحي", max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    is_active = models.BooleanField("نشطة", default=True)

    class Meta:
        verbose_name = "محفظة"
        verbose_name_plural = "المحافظ"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.phone_number}"

    def current_balance(self):
        incoming = (
            self.transactions.filter(transaction_type=Transaction.CUSTOMER_PAYMENT).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )
        transferred = (
            self.transactions.filter(transaction_type=Transaction.WALLET_TO_BANK).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )
        fees = self.transactions.aggregate(total=Sum("fee"))["total"] or Decimal("0.00")
        return self.opening_balance + incoming - transferred - fees


class BankAccount(TimeStampedModel):
    bank_name = models.CharField("اسم البنك", max_length=120)
    account_name = models.CharField("اسم الحساب", max_length=120)
    account_number = models.CharField("رقم الحساب", max_length=80)
    notes = models.TextField("ملاحظات", blank=True)
    is_active = models.BooleanField("نشط", default=True)

    class Meta:
        verbose_name = "حساب بنكي"
        verbose_name_plural = "الحسابات البنكية"
        ordering = ["bank_name", "account_name"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_name}"


class Transaction(TimeStampedModel):
    CUSTOMER_PAYMENT = "customer_payment"
    WALLET_TO_BANK = "wallet_to_bank"

    TRANSACTION_TYPES = [
        (CUSTOMER_PAYMENT, "وارد من عميل"),
        (WALLET_TO_BANK, "تحويل إلى البنك"),
    ]

    transaction_type = models.CharField(
        "نوع العملية", max_length=30, choices=TRANSACTION_TYPES, default=CUSTOMER_PAYMENT
    )
    wallet = models.ForeignKey(
        Wallet, verbose_name="المحفظة", on_delete=models.PROTECT, related_name="transactions"
    )
    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="الحساب البنكي",
        on_delete=models.PROTECT,
        related_name="transactions",
        null=True,
        blank=True,
    )
    customer_name = models.CharField("اسم العميل", max_length=120, blank=True)
    customer_phone = models.CharField("رقم العميل", max_length=30, blank=True)
    amount = models.DecimalField("المبلغ", max_digits=14, decimal_places=2)
    fee = models.DecimalField("العمولة", max_digits=14, decimal_places=2, default=Decimal("0.00"))
    net_amount = models.DecimalField(
        "الصافي", max_digits=14, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    reference_number = models.CharField("رقم العملية", max_length=120, blank=True)
    transaction_date = models.DateTimeField("تاريخ العملية")
    receipt_image = models.FileField(
        "صورة الإيصال",
        upload_to="receipts/%Y/%m/",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
    )
    notes = models.TextField("ملاحظات", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="أضيفت بواسطة",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_transactions",
    )

    class Meta:
        verbose_name = "عملية"
        verbose_name_plural = "العمليات"
        ordering = ["-transaction_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["reference_number"],
                condition=~Q(reference_number=""),
                name="unique_non_empty_reference_number",
            )
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"

    def clean(self):
        errors = {}

        if self.amount is not None and self.amount <= 0:
            errors["amount"] = "المبلغ يجب أن يكون أكبر من صفر."

        if self.fee is not None and self.fee < 0:
            errors["fee"] = "العمولة لا يمكن أن تكون أقل من صفر."

        if self.amount is not None and self.fee is not None and self.amount - self.fee < 0:
            errors["fee"] = "الصافي لا يمكن أن يكون أقل من صفر."

        if self.transaction_type == self.WALLET_TO_BANK and not self.bank_account:
            errors["bank_account"] = "الحساب البنكي مطلوب عند التحويل إلى البنك."

        if self.reference_number:
            duplicate = Transaction.objects.filter(reference_number=self.reference_number)
            if self.pk:
                duplicate = duplicate.exclude(pk=self.pk)
            if duplicate.exists():
                errors["reference_number"] = "رقم العملية مستخدم من قبل."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.net_amount = (self.amount or Decimal("0.00")) - (self.fee or Decimal("0.00"))
        if self.transaction_type == self.CUSTOMER_PAYMENT:
            self.bank_account = None
        if self.transaction_type == self.WALLET_TO_BANK:
            self.customer_name = ""
            self.customer_phone = ""
        super().save(*args, **kwargs)


class SystemSettings(TimeStampedModel):
    company_name = models.CharField(
        "اسم الشركة", max_length=160, default="نظام متابعة المحافظ الإلكترونية"
    )
    company_logo = models.FileField(
        "شعار الشركة",
        upload_to="settings/",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
    )
    default_currency = models.CharField("العملة الافتراضية", max_length=30, default="جنيه")
    backup_directory = models.CharField("مسار حفظ النسخ الاحتياطية", max_length=500, blank=True)
    notes = models.TextField("ملاحظات عامة", blank=True)

    class Meta:
        verbose_name = "إعدادات النظام"
        verbose_name_plural = "إعدادات النظام"

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        settings_obj, _ = cls.objects.get_or_create(pk=1)
        return settings_obj
