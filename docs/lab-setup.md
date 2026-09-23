# Environnement de laboratoire

- Cible : VM Windows 11 x64 dans VMware.
- Réseau recommandé : host-only ou réseau privé, sans accès aux systèmes de production.
- Snapshot : créer un snapshot propre avant chaque série de tests.
- Hôte de développement : Python 3.11 et le dépôt du projet.
- Vérification : lancer le contrôleur et l'agent sur `127.0.0.1`, puis observer les connexions avec les journaux locaux.

La démonstration ne doit pas utiliser de comptes réels, de fichiers personnels ou de secrets. Les événements de compromission sont synthétiques.
