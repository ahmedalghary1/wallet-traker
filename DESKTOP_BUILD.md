# تجهيز نسخة Desktop احترافية

## مكان البيانات بعد التعديل

عند تشغيل النظام في وضع Desktop يتم تخزين البيانات خارج مجلد تثبيت البرنامج، داخل:

```text
%LOCALAPPDATA%\Wallet Tracker
```

ويتم إنشاء الملفات التالية تلقائيًا:

```text
%LOCALAPPDATA%\Wallet Tracker\db.sqlite3
%LOCALAPPDATA%\Wallet Tracker\media
%LOCALAPPDATA%\Wallet Tracker\logs\wallet_tracker.log
```

هذا مهم لأن مجلد تثبيت التطبيق قد يكون للقراءة فقط، ولأن تحديث البرنامج لا يجب أن يحذف قاعدة بيانات العميل.

## تشغيل backend بدون Electron

بعد تثبيت المتطلبات:

```powershell
pip install -r requirements.txt
```

شغل خادم Django المحلي بوضع Desktop:

```powershell
python run_app.py --host 127.0.0.1 --port 8000
```

هذا الأمر يستخدم Waitress بدل `runserver`، ويطبق migrations عند الحاجة فقط، بدون تشغيل `makemigrations` في كل مرة.
واجهة التطبيق المحلي تعمل مباشرة بدون شاشة تسجيل دخول لأنها مخصصة لجهاز واحد.

## بناء ملف backend التنفيذي

من مجلد المشروع الرئيسي:

```powershell
python -m PyInstaller --noconfirm --distpath electron_app/backend --workpath build/pyinstaller wallet_backend.spec
```

سيتم إنشاء مجلد backend هنا:

```text
electron_app\backend\wallet_backend\wallet_backend.exe
```

## تشغيل Electron أثناء التطوير

من مجلد `electron_app`:

```powershell
npm.cmd install
npm.cmd start
```

في وضع التطوير، Electron يشغل:

```text
python run_app.py --host 127.0.0.1 --port <free-port>
```

## بناء تطبيق Windows كامل

من مجلد `electron_app`:

```powershell
npm.cmd run build
```

الأمر ينفذ خطوتين:

```text
1. بناء wallet_backend.exe باستخدام PyInstaller
2. بناء مثبت Windows باستخدام electron-builder
```

البناء الحالي غير موقّع رقميًا حتى يعمل على أجهزة التطوير التي لا تسمح بإنشاء symlinks المطلوبة لأداة `winCodeSign`. عند توفر شهادة توقيع للشركة يمكن إزالة `signAndEditExecutable: false` من `electron_app/package.json` وإضافة إعدادات التوقيع.

## ملاحظات أداء

- لا يتم تشغيل `makemigrations` عند فتح التطبيق، لأن ذلك بطيء وغير مناسب للإنتاج.
- Electron يختار منفذًا محليًا فارغًا بدل الاعتماد على `8000` دائمًا.
- يتم منع فتح أكثر من نسخة من التطبيق في نفس الوقت لحماية SQLite من التعارض.
- قاعدة البيانات والملفات المرفوعة تبقى في AppLocal ولا تتأثر بتحديث التطبيق.
