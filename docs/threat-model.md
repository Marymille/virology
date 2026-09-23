# Modèle de menace

## Actifs

- La VM Windows 11 de démonstration.
- Les journaux du contrôleur.
- L'intégrité du dépôt et des tests.

## Menaces étudiées

- Commande non autorisée envoyée à l'agent.
- Agent qui tente de contacter une adresse externe.
- Message réseau malformé.
- Présence d'événements ressemblant à une compromission.

## Mesures

- Liste blanche de trois commandes.
- Écoute limitée à `127.0.0.1`.
- Refus des commandes inconnues.
- Messages JSON validés avant traitement.
- Données de démonstration synthétiques.
- Tests automatisés et snapshot de VM.
