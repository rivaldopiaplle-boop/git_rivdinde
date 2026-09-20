# Toute l'API est versionnee des le depart : le jour ou une charge utile doit
# changer sans casser une application mobile deja installee, /api/v2 cohabite
# avec /api/v1 au lieu de la remplacer.
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("coeur.urls")),
    path("api/v1/", include("comptes.urls")),
    path("api/v1/", include("catalogue.urls")),
    path("api/v1/", include("commandes.urls")),
]

# En developpement, Django sert lui-meme les images televersees. En ligne,
# elles sont chez Cloudinary et cette ligne ne s'applique jamais (D-24).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
