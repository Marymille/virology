# Presentation - s0P0wn3d

## 1. Contexte

- Projet Virology realise dans un laboratoire controle.
- Objectif : comprendre le modele agent-controleur et les traces observables.
- Cible de demonstration : VM Windows 11 x64.

## 2. Architecture

```text
[Agent Python] <-- JSON sur localhost --> [Controleur Python]
                                      |
                                      +--> [Interface web locale]
```

- `agent/agent.py` : agent de simulation persistant pendant la demonstration.
- `controller/app.py` : controleur en ligne de commande.
- `controller/web.py` : tableau de bord local.
- `common/protocol.py` : messages et liste blanche de commandes.

## 3. Demonstration

1. Lancer `python -m controller.web`.
2. Lancer `python -m agent.agent` dans un second terminal.
3. Ouvrir `http://127.0.0.1:8080`.
4. Executer `status`, `heartbeat`, puis `get_demo_log`.
5. Montrer l'etat de connexion et l'historique.

## 4. Mesures de securite

- Ecoute limitee a `127.0.0.1`.
- Trois commandes autorisees seulement.
- Aucun shell arbitraire.
- Aucune collecte reelle de secrets.
- Evenements de compromission synthetiques.
- Tests automatises et snapshot de VM.

## 5. Analyse Blue Team

- Traces reseau locales et ports ouverts.
- Identite de l'agent et horodatage des commandes.
- Validation des commandes inattendues.
- Possibilite de comparer les comportements normaux et anormaux.

## 6. Bilan

Le projet demontre le cycle complet d'une commande dans un environnement reproductible, tout en gardant les capacites dangereuses hors du prototype. Les limites sont documentees et peuvent etre discutees du point de vue defense.
