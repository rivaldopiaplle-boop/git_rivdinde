#!/usr/bin/env python
# Point d'entree des commandes Django.
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as erreur:
        raise ImportError(
            "Django est introuvable. Environnement virtuel active ? "
            "Depuis backend/ : python -m venv .venv puis .venv\\Scripts\\Activate.ps1"
        ) from erreur
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
