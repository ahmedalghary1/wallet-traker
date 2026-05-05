from django.contrib import admin

from .models import BankAccount, SystemSettings, Transaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "wallet_type",
        "phone_number",
        "opening_balance",
        "current_balance",
        "is_active",
    )
    list_filter = ("wallet_type", "is_active")
    search_fields = ("name", "phone_number")


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("bank_name", "account_name", "account_number", "is_active")
    list_filter = ("is_active",)
    search_fields = ("bank_name", "account_name", "account_number")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_date",
        "transaction_type",
        "wallet",
        "bank_account",
        "amount",
        "fee",
        "net_amount",
        "reference_number",
        "created_by",
    )
    list_filter = ("transaction_type", "wallet", "bank_account", "transaction_date")
    search_fields = ("customer_name", "customer_phone", "reference_number")
    readonly_fields = ("net_amount", "created_at", "updated_at")


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("company_name", "default_currency", "updated_at")
