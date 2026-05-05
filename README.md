# نظام متابعة المحافظ الإلكترونية

نظام Django بسيط لإدارة المحافظ الإلكترونية والتحويلات والعمولات والتقارير، مع واجهة عربية RTL وتجهيز لتطبيق سطح مكتب عبر Electron.

## تشغيل نسخة الويب

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

افتح:

```text
http://127.0.0.1:8000/
```

لا توجد شاشة تسجيل دخول في واجهة التطبيق؛ النظام يعمل مباشرة كوضع محلي لجهاز واحد.

## تشغيل نسخة Desktop أثناء التطوير

من مجلد `electron_app`:

```powershell
npm.cmd install
npm.cmd start
```

في وضع التطوير، Electron يشغل `run_app.py` تلقائيًا على منفذ محلي فارغ.

## مكان بيانات نسخة Desktop

عند تشغيل `run_app.py` أو Electron في وضع Desktop، يتم حفظ قاعدة البيانات والملفات داخل:

```text
%LOCALAPPDATA%\Wallet Tracker
```

وليس داخل مجلد تثبيت البرنامج.

## بناء backend باستخدام PyInstaller

من مجلد المشروع الرئيسي:

```powershell
python -m PyInstaller --noconfirm wallet_backend.spec
```

سيتم إنشاء:

```text
electron_app\backend\wallet_backend\wallet_backend.exe
```

## بناء تطبيق Windows كامل

من مجلد `electron_app`:

```powershell
npm.cmd run build
```

هذا الأمر يبني `wallet_backend.exe` أولًا، ثم يبني مثبت Windows عبر `electron-builder`.

## تفاصيل أكثر

راجع:

```text
DESKTOP_BUILD.md
```
