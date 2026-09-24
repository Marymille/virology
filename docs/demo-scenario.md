# Scenario de demonstration

## Objectif

Montrer le fonctionnement d'un agent et d'un controleur locaux dans une VM Windows 11, puis expliquer les observations cote defense.

## Preparation

1. Restaurer le snapshot `clean-lab-before-demo`.
2. Ouvrir PowerShell dans le dossier du projet.
3. Activer l'environnement virtuel : `./.venv/Scripts/Activate.ps1`.
4. Verifier les tests : `python -m pytest -q`.

## Demonstration web

Dans le premier terminal :

```powershell
python -m controller.web
```

Dans le deuxieme terminal :

```powershell
python -m agent.agent
```

Ouvrir `http://127.0.0.1:8080` et executer successivement `Etat`, `Heartbeat` et `Journal de demo`.

## Demonstration TLS

Generer une paire de fichiers de laboratoire :

```powershell
python -m tools.generate_cert --output-dir certs
```

Dans le premier terminal :

```powershell
python -m controller.web --tls --web-port 8443
```

Dans le deuxieme terminal :

```powershell
python -m agent.agent --tls
```

Ouvrir `https://127.0.0.1:8443`. Le navigateur peut afficher un avertissement, car le certificat est auto-signe et reserve au laboratoire.

Dans Wireshark, filtrer `tcp.port == 8765` et verifier que les messages JSON ne sont pas lisibles sur le reseau : seul le flux TLS est observable.

## Resultats attendus

- L'interface indique `Agent : connecte`.
- Chaque commande autorisee retourne un resultat JSON.
- L'historique indique la commande et son horodatage.
- Une commande inconnue est refusee par la validation.

## Analyse defensive

Observer les connexions locales, les ports d'ecoute et les journaux du controleur. Expliquer qu'un vrai SOC rechercherait des connexions inhabituelles, des processus inattendus et des commandes non conformes au profil de la machine.

## Fin de session

Arreter les deux processus avec `Ctrl+C`, puis restaurer le snapshot si necessaire. Aucun secret, fichier personnel ou compte reel ne doit etre utilise pendant la demonstration.
