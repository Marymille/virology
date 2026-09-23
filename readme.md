# s0P0wn3d - démonstrateur C2 contrôlé

Ce projet est un démonstrateur pédagogique exécuté uniquement dans une VM de laboratoire. Il ne fournit ni shell arbitraire, ni collecte réelle d'identifiants, ni keylogging, ni persistance, ni évasion antivirus.

## Installation sous Windows 11

Dans PowerShell, à la racine du projet :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Démonstration

Ouvrir deux terminaux dans la racine du projet. Dans le premier :

```powershell
python -m controller.app status
```

Dans le second :

```powershell
python -m agent.agent
```

Tester aussi `heartbeat` et `get_demo_log`. Le contrôleur écoute uniquement sur `127.0.0.1` et les commandes non prévues sont refusées.

## Organisation

- `common/protocol.py` : messages JSON et validation des commandes.
- `agent/agent.py` : agent de simulation limité à trois commandes.
- `controller/app.py` : contrôleur local pour la démonstration.
- `tests/` : tests automatisés.
- `docs/` : environnement, modèle de menace et analyse défense.

## Limites et éthique

La VM doit rester isolée et être restaurée depuis un snapshot après les essais. Toute expérimentation sur une machine ou un réseau tiers nécessite une autorisation écrite.
