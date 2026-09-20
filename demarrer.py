#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tout demarrer, en une commande.

    python demarrer.py

Quatre choses doivent tourner ensemble : la base Postgres, l'attrapeur de
courriels, l'API Django et le front Vue. Lancees a la main, il faut se
rappeler de l'ordre, et l'oubli d'une seule produit dix minutes plus tard une
erreur incomprehensible.

Ce script fait la meme chose, dans le bon ordre, et **attend reellement** que
chaque service reponde avant de lancer le suivant. Il prepare aussi ce qui
manque : interpreteur, environnement virtuel, dependances, .env, migrations.

    --etat          ne demarre rien : dit ce qui tourne et ce qui repond
    --sans-web      ne lance pas le front Vue
    --preparer      installe et migre, puis rend la main sans rien lancer
    --arreter       arrete les conteneurs

Ports utilises : 5433 (base), 1026 et 8026 (courriels), 8000 (API), 5173
(front). Ils sont decales de ceux du projet banque, qui occupe deja 5432,
1025 et 8025 sur cette machine : les deux projets tournent en meme temps
sans se marcher dessus.

Ce script ne sert qu'en developpement. En ligne, chaque morceau est deploye
separement et supervise par son hebergeur — raison pour laquelle il tient en
un fichier, sans aucune dependance a installer.
"""
import os
import platform
import re
import shutil
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(RACINE, "backend")
WEB = os.path.join(RACINE, "frontend-web")
WINDOWS = platform.system() == "Windows"

PYTHON_MINIMUM = (3, 10)  # Django 5 n'accepte pas moins


# ── Affichage ────────────────────────────────────────────────────────────
# Les codes couleur ANSI sont compris par Windows Terminal et PowerShell ;
# sur une console plus ancienne ils s'affichent en clair, ce qui reste lisible.

def _c(code, texte):
    return "\033[%sm%s\033[0m" % (code, texte)


def etape(t):
    print("\n" + _c("1", "-- " + t))


def ok(t):
    print("   " + _c("32", "OK") + "  " + t)


def info(t):
    print("   " + _c("2", t))


def echec(t):
    print("   " + _c("31", "!!") + "  " + t)


def fatal(titre, quoi_faire):
    print("\n" + _c("31", "ARRET : " + titre))
    for ligne in quoi_faire.split("\n"):
        print("        " + ligne)
    print("")
    sys.exit(1)


# ── Outils ───────────────────────────────────────────────────────────────

def executer(commande, cwd=RACINE, silencieux=True):
    """Lance une commande et attend la fin. Renvoie (code, sortie)."""
    resultat = subprocess.run(
        commande,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE if silencieux else None,
        stderr=subprocess.STDOUT if silencieux else None,
    )
    sortie = ""
    if silencieux and resultat.stdout:
        sortie = resultat.stdout.decode("utf-8", "replace")
    return resultat.returncode, sortie


def disponible(programme):
    return shutil.which(programme) is not None


def repond(url, timeout=2):
    """Vrai si l'adresse repond, quel que soit le code HTTP."""
    try:
        from urllib.request import urlopen
        urlopen(url, timeout=timeout).read()
        return True
    except Exception as erreur:
        # Une reponse 4xx ou 5xx prouve quand meme que quelque chose ecoute.
        return hasattr(erreur, "code")


def python_du_venv():
    if WINDOWS:
        return os.path.join(BACKEND, ".venv", "Scripts", "python.exe")
    return os.path.join(BACKEND, ".venv", "bin", "python")


# ── Trouver un interpreteur convenable ───────────────────────────────────
#
# Cas tres frequent sous Windows : PowerShell voit Python 3.14 pendant que
# Git Bash voit encore un 3.8 installe des annees plus tot. Plutot que de
# renvoyer l'utilisateur a sa variable PATH, on demande au lanceur `py`,
# qui connait toutes les versions installees, et on repart avec la bonne.

def version_de(python):
    """Renvoie (majeur, mineur) d'un interpreteur, ou None s'il ne repond pas."""
    code, sortie = executer(
        '"%s" -c "import sys; print(sys.version_info[0], sys.version_info[1])"' % python
    )
    if code != 0:
        return None
    try:
        majeur, mineur = sortie.split()[:2]
        return (int(majeur), int(mineur))
    except (ValueError, IndexError):
        return None


def chercher_python_convenable():
    """Le Python le plus recent installe sur la machine, s'il convient."""
    if sys.version_info >= PYTHON_MINIMUM:
        return sys.executable

    code, sortie = executer("py -0p")
    if code != 0:
        return None

    # Une ligne de `py -0p` ressemble a :
    #     -V:3.14 *        C:\\Program Files\\Python314\\python.exe
    motif = re.compile(r"-V:(\d+)\.(\d+)\S*\s+\*?\s*(.+?\.exe)\s*$")

    candidats = []
    for ligne in sortie.splitlines():
        trouve = motif.search(ligne)
        if not trouve:
            continue
        version = (int(trouve.group(1)), int(trouve.group(2)))
        chemin = trouve.group(3).strip()
        if version >= PYTHON_MINIMUM and os.path.exists(chemin):
            candidats.append((version, chemin))

    return max(candidats)[1] if candidats else None


def relancer_avec_un_python_recent():
    """Si l'interpreteur courant est trop vieux, se relance avec un bon."""
    if sys.version_info >= PYTHON_MINIMUM:
        return

    meilleur = chercher_python_convenable()
    if not meilleur:
        fatal(
            "Python %d.%d, il en faut au moins %d.%d"
            % (sys.version_info[0], sys.version_info[1],
               PYTHON_MINIMUM[0], PYTHON_MINIMUM[1]),
            "Django 5 exige Python 3.10 ou plus. Installe-le depuis "
            "python.org,\ncoche l'ajout au PATH, ouvre un NOUVEAU terminal, "
            "puis relance.",
        )

    version = version_de(meilleur) or (0, 0)
    info("Ce terminal utilise Python %d.%d, trop ancien pour Django 5."
         % (sys.version_info[0], sys.version_info[1]))
    info("Python %d.%d est installe : %s" % (version[0], version[1], meilleur))
    info("On repart avec celui-la.")
    # Sans ce vidage, les lignes ci-dessus sortent APRES celles du processus
    # enfant : le message expliquant le changement d interpreteur arriverait
    # a la fin, quand il ne sert plus a rien.
    sys.stdout.flush()
    sys.exit(subprocess.call([meilleur, os.path.abspath(__file__)] + sys.argv[1:]))


# ── Verifications prealables ─────────────────────────────────────────────

def verifier_outils():
    etape("Verification des outils")

    ok("Python %d.%d.%d" % sys.version_info[:3])

    if not disponible("docker"):
        fatal(
            "Docker est introuvable",
            "Installe Docker Desktop, lance-le, et attends que son icone\n"
            "soit stable avant de relancer.",
        )
    code, _ = executer("docker info")
    if code != 0:
        fatal(
            "Docker est installe mais ne repond pas",
            "Docker Desktop est-il demarre ? Son icone doit etre stable,\n"
            "pas en cours de demarrage.",
        )
    ok("Docker repond")

    if not disponible("node"):
        info("Node est introuvable : le front web ne sera pas lance.")
        return False
    ok("Node " + executer("node --version")[1].strip())
    return True


# ── Les conteneurs ───────────────────────────────────────────────────────

def demarrer_conteneurs():
    etape("Base de donnees et attrapeur de courriels")

    code, sortie = executer("docker compose up -d")
    if code != 0:
        echec("docker compose a echoue :")
        print(sortie)
        if "port is already allocated" in sortie or "address already in use" in sortie:
            fatal(
                "Un port est deja pris",
                "Un autre projet occupe un des ports de RivDinde.\n"
                "Voir qui : docker ps\n"
                "Les ports de RivDinde sont 5433, 1026 et 8026 — ils sont deja\n"
                "decales de ceux du projet banque (5432, 1025, 8025).",
            )
        fatal("Les conteneurs n'ont pas demarre", "Lis le message ci-dessus.")

    # On attend que Postgres accepte reellement les connexions : sans cela,
    # les migrations partent trop tot et l'erreur est illisible.
    info("Attente de Postgres…")
    for _ in range(40):
        code, sortie = executer(
            'docker inspect --format "{{.State.Health.Status}}" rivdinde-base'
        )
        if "healthy" in sortie:
            ok("Postgres accepte les connexions (port 5433)")
            return
        time.sleep(1)

    fatal(
        "Postgres n'a pas repondu en 40 secondes",
        "Voir les journaux : docker compose logs base",
    )


# ── Le backend ───────────────────────────────────────────────────────────

def preparer_backend():
    etape("API Django")

    fichier_env = os.path.join(BACKEND, ".env")
    if not os.path.exists(fichier_env):
        shutil.copyfile(os.path.join(BACKEND, ".env.example"), fichier_env)
        ok("backend/.env cree depuis .env.example (aucune cle requise pour demarrer)")

    py = python_du_venv()

    # Un environnement virtuel garde l'interpreteur avec lequel il a ete cree.
    # S'il a ete fabrique par un Python devenu trop vieux, le refaire coute
    # trente secondes ; le garder coute une erreur incomprehensible plus tard.
    if os.path.exists(py):
        version = version_de(py)
        if version is None or version < PYTHON_MINIMUM:
            info("L'environnement virtuel existant est perime : on le refait.")
            shutil.rmtree(os.path.join(BACKEND, ".venv"), ignore_errors=True)

    if not os.path.exists(py):
        info("Creation de l'environnement virtuel…")
        code, sortie = executer('"%s" -m venv .venv' % sys.executable, cwd=BACKEND)
        if code != 0:
            echec(sortie)
            fatal("L'environnement virtuel n'a pas ete cree", "Lis le message ci-dessus.")
        ok("backend/.venv cree")

    # `pip install` est rejoue a chaque fois : c'est quasi instantane quand
    # rien n'a change, et cela evite le grand classique « ca marchait hier »
    # apres l'ajout d'une dependance.
    info("Installation des dependances Python…")
    code, sortie = executer(
        '"%s" -m pip install -q --disable-pip-version-check -r requirements-dev.txt' % py,
        cwd=BACKEND,
    )
    if code != 0:
        echec(sortie[-1500:])
        fatal("Les dependances n'ont pas pu etre installees", "Lis le message ci-dessus.")
    ok("Dependances a jour")

    info("Application des migrations…")
    code, sortie = executer('"%s" manage.py migrate --noinput' % py, cwd=BACKEND)
    if code != 0:
        echec(sortie[-1500:])
        fatal("Les migrations ont echoue", "Lis le message ci-dessus.")
    ok("Base a jour")

    # Sans compte administrateur, /admin/ demande des identifiants que
    # personne ne possede. La commande est idempotente et ne touche pas au
    # mot de passe d'un compte deja en place.
    code, sortie = executer('"%s" manage.py seed_admin' % py, cwd=BACKEND)
    if code != 0:
        echec("La creation du compte administrateur a echoue :")
        print(sortie[-800:])
    else:
        for ligne in sortie.strip().splitlines():
            if ligne.strip():
                info(ligne.rstrip())

    # Les comptes de demonstration. Idempotent : ne touche a rien s'ils sont
    # deja la. C'est ce qui permet de derouler un scenario du dossier de
    # conception a l'ecran, sans rien saisir a la main.
    code, sortie = executer('"%s" manage.py seed_demo' % py, cwd=BACKEND)
    if code != 0:
        echec("Le jeu de demonstration n'a pas pu etre cree :")
        print(sortie[-800:])
    else:
        for ligne in sortie.strip().splitlines():
            if ligne.strip():
                info(ligne.rstrip())


def preparer_web():
    etape("Front web Vue")

    fichier_env = os.path.join(WEB, ".env")
    if not os.path.exists(fichier_env):
        shutil.copyfile(os.path.join(WEB, ".env.example"), fichier_env)
        ok("frontend-web/.env cree depuis .env.example")

    if not os.path.isdir(os.path.join(WEB, "node_modules")):
        info("Installation des dependances npm (une seule fois, soyons patients)…")
        code, sortie = executer("npm install --no-fund --no-audit", cwd=WEB)
        if code != 0:
            echec(sortie[-1500:])
            fatal("npm install a echoue", "Lis le message ci-dessus.")
    ok("Dependances npm en place")


# ── Lancement ────────────────────────────────────────────────────────────

def lancer(avec_web):
    etape("Demarrage")

    processus = []

    api = subprocess.Popen(
        '"%s" manage.py runserver 0.0.0.0:8000' % python_du_venv(),
        cwd=BACKEND,
        shell=True,
    )
    processus.append(("API", api))

    for _ in range(30):
        if repond("http://localhost:8000/api/v1/sante"):
            ok("API                    http://localhost:8000/api/v1/sante")
            break
        time.sleep(1)
    else:
        echec("L'API n'a pas repondu en 30 secondes — voir sa sortie ci-dessus.")

    if avec_web:
        web = subprocess.Popen("npm run dev", cwd=WEB, shell=True)
        processus.append(("Front web", web))
        for _ in range(30):
            if repond("http://localhost:5173"):
                ok("Front web              http://localhost:5173")
                break
            time.sleep(1)

    ok("Administration Django  http://localhost:8000/admin/")
    ok("Courriels captures     http://localhost:8026")

    print("\n" + _c("1", "Tout tourne.") + " Ctrl+C pour arreter.\n")

    try:
        while True:
            time.sleep(1)
            for nom, p in processus:
                if p.poll() is not None:
                    echec("%s s'est arrete (code %s)." % (nom, p.returncode))
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("\nArret…")
        for _, p in processus:
            try:
                p.terminate()
            except Exception:
                pass
        info("Les conteneurs continuent de tourner.")
        info("Pour les arreter : python demarrer.py --arreter")


# ── Etat ─────────────────────────────────────────────────────────────────

def etat():
    etape("Etat des services")
    controles = [
        ("Base Postgres", "docker", "rivdinde-base"),
        ("Courriels (Mailpit)", "http", "http://localhost:8026"),
        ("API Django", "http", "http://localhost:8000/api/v1/sante"),
        ("Front web", "http", "http://localhost:5173"),
    ]
    for nom, genre, cible in controles:
        if genre == "docker":
            _, sortie = executer('docker ps --filter "name=%s" --format "{{.Names}}"' % cible)
            vivant = cible in sortie
        else:
            vivant = repond(cible)
        (ok if vivant else echec)("%-22s %s" % (nom, "en ligne" if vivant else "eteint"))


# ── Point d'entree ───────────────────────────────────────────────────────

def main():
    options = set(sys.argv[1:])

    print(_c("1", "\n  RivDinde") + _c("2", " — commander, livrer, suivre"))

    if "--arreter" in options:
        etape("Arret des conteneurs")
        executer("docker compose down", silencieux=False)
        return

    if "--etat" in options:
        etat()
        return

    relancer_avec_un_python_recent()

    node_present = verifier_outils()
    avec_web = node_present and "--sans-web" not in options

    demarrer_conteneurs()
    preparer_backend()
    if avec_web:
        preparer_web()

    if "--preparer" in options:
        print("\n" + _c("1", "Tout est pret.") + " Relance sans --preparer pour demarrer.\n")
        return

    lancer(avec_web)


if __name__ == "__main__":
    main()
