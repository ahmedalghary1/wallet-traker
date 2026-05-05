from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("login/", views.local_app_redirect, name="login"),
    path("logout/", views.local_app_redirect, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/add/", views.transaction_add, name="transaction_add"),
    path("transactions/<int:pk>/", views.transaction_detail, name="transaction_detail"),
    path("transactions/<int:pk>/edit/", views.transaction_edit, name="transaction_edit"),
    path("transactions/<int:pk>/delete/", views.transaction_delete, name="transaction_delete"),
    path("wallets/", views.wallet_list, name="wallet_list"),
    path("wallets/add/", views.wallet_add, name="wallet_add"),
    path("wallets/<int:pk>/edit/", views.wallet_edit, name="wallet_edit"),
    path("wallets/<int:pk>/delete/", views.wallet_delete, name="wallet_delete"),
    path("banks/", views.bank_list, name="bank_list"),
    path("banks/add/", views.bank_add, name="bank_add"),
    path("banks/<int:pk>/edit/", views.bank_edit, name="bank_edit"),
    path("banks/<int:pk>/delete/", views.bank_delete, name="bank_delete"),
    path("reports/", views.reports, name="reports"),
    path("reports/export-excel/", views.export_report_excel, name="export_report_excel"),
    path("backup/create/", views.create_backup, name="create_backup"),
    path("settings/", views.system_settings, name="system_settings"),
]
