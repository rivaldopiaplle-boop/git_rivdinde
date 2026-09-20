# Image de l'API. Multi-etapes volontairement evite : Django n'a rien a
# compiler, et une seule etape reste plus simple a lire.
FROM python:3.14-slim

# Ne pas ecrire de .pyc, ne pas tamponner la sortie : les journaux de
# l'hebergeur s'affichent alors en temps reel au lieu d'arriver par paquets.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Les dependances d'abord : tant que requirements.txt ne change pas, Docker
# reutilise cette couche et la reconstruction prend deux secondes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Un utilisateur sans privileges : si l'application est compromise, elle n'est
# pas root dans son conteneur.
RUN adduser --disabled-password --gecos "" rivdinde && chown -R rivdinde /app
USER rivdinde

EXPOSE 8000

# collectstatic au demarrage plutot qu'a la construction : l'image reste
# utilisable telle quelle en local, ou les fichiers statiques sont servis
# autrement. `migrate` est lance ici pour qu'une mise en ligne n'exige jamais
# une commande manuelle en production.
CMD python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60
