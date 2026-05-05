from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.static import serve


urlpatterns = [
    path("", include("core.urls")),
]

if settings.DEBUG or getattr(settings, "DESKTOP_LOCAL_MODE", False):
    if settings.STATICFILES_DIRS:
        urlpatterns += [
            re_path(
                r"^static/(?P<path>.*)$",
                serve,
                {"document_root": settings.STATICFILES_DIRS[0]},
            )
        ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
