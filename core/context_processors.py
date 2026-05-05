def system_settings(request):
    try:
        from .models import SystemSettings

        return {"system_settings": SystemSettings.load()}
    except Exception:
        return {"system_settings": None}
