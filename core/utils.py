from decimal import Decimal

from django.db.models import Q, Sum
from django.utils.dateparse import parse_date

from .models import Transaction


def money_total(queryset, field):
    return queryset.aggregate(total=Sum(field))["total"] or Decimal("0.00")


def transaction_totals(queryset):
    return {
        "amount": money_total(queryset, "amount"),
        "fees": money_total(queryset, "fee"),
        "net": money_total(queryset, "net_amount"),
        "count": queryset.count(),
    }


def filtered_transactions(params, base_queryset=None):
    queryset = base_queryset or Transaction.objects.select_related("wallet", "bank_account")

    date_from = parse_date(params.get("date_from") or "")
    date_to = parse_date(params.get("date_to") or "")
    transaction_type = params.get("transaction_type") or ""
    wallet_id = params.get("wallet") or ""
    bank_id = params.get("bank") or ""
    query = (params.get("q") or "").strip()

    if date_from:
        queryset = queryset.filter(transaction_date__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(transaction_date__date__lte=date_to)
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)
    if wallet_id:
        queryset = queryset.filter(wallet_id=wallet_id)
    if bank_id:
        queryset = queryset.filter(bank_account_id=bank_id)
    if query:
        queryset = queryset.filter(
            Q(customer_name__icontains=query)
            | Q(customer_phone__icontains=query)
            | Q(reference_number__icontains=query)
        )

    return queryset
