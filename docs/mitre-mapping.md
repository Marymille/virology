# Cartographie MITRE ATT&CK

## Perimetre

Cette cartographie sert a analyser les comportements et leurs detections. Le prototype reste un simulateur local : il n'execute pas de commande systeme, ne collecte pas de secrets et ne contacte aucune machine externe.

La tactique principalement etudiee est **Command and Control (`TA0011`)**. Les references ci-dessous decrivent des techniques ATT&CK associees au sujet, pas des capacites offensives implementees.

## Capacites effectivement demontrees

| Element du prototype | Reference ATT&CK | Statut | Note Blue Team |
| --- | --- | --- | --- |
| Echange agent-controleur sur TCP local | `TA0011` / `T1071.001` | Simulation locale | Surveiller les connexions sortantes, le processus a l'origine du flux et les destinations inhabituelles. |
| Echange chiffre en TLS | `TA0011` / `T1573.001` | TLS de laboratoire | Inspecter les metadonnees TLS, les certificats, les destinations et les anomalies de volume. |
| Reception d'une commande liste blanche | `TA0011` / `T1059` | Simulation uniquement | Journaliser l'identite de l'agent, l'heure, la commande et le resultat. |
| Heartbeat et etat d'un agent | `TA0011` / `T1071.001` | Donnees fictives | Rechercher un beaconing regulier et comparer la periodicite au comportement habituel. |
| Journal d'audit du controleur | Detection defensive | Implemente | Proteger les journaux contre la modification et centraliser les evenements. |
| Kill switch de laboratoire | Mesure defensive | Implemente | Permettre l'isolement rapide de la session et conserver la trace de l'action. |

## Capacites du sujet representees par des evenements synthetiques

| Capacite etudiee | Reference ATT&CK | Representation dans le prototype | Note Blue Team |
| --- | --- | --- | --- |
| Shell distant | `T1059` | Aucune execution ; commandes inconnues refusees | Alerter sur les interpreteurs inattendus, les arguments inhabituels et les chaines parent-enfant. |
| Acces aux identifiants | `T1003` | Evenement de journal fictif uniquement | Surveiller les acces a LSASS, aux magasins d'identifiants et aux fichiers sensibles. |
| Keylogging | `T1056.001` | Non implemente | Detecter les processus qui utilisent des API de capture clavier et leurs connexions sortantes. |
| Persistance | `T1547` | Evenement synthetique uniquement | Auditer les cles de demarrage, services et taches planifiees. |
| Chiffrement des communications | `T1573` | TLS local implemente | Verifier la version TLS, le certificat et les suites cryptographiques autorisees. |
| Phishing | `T1566` | Non implemente | Utiliser la protection messagerie, l'analyse des liens et l'authentification forte. |
| Propagation laterale | `T1021` / `T1570` | Non implemente | Limiter les flux est-ouest et journaliser l'utilisation des services distants. |
| Elevation de privileges | `T1068` / `T1548` | Non implemente | Appliquer le moindre privilege et surveiller les changements de contexte. |
| Appels API natifs | `T1106` | Non implemente | Corréler les appels sensibles avec le processus, le parent et le comportement reseau. |
| Obfuscation et evasions | `T1027` | Non implemente | Utiliser l'analyse comportementale et l'integrite des binaires, pas seulement les signatures. |

## Limites et preuves

- Les commandes autorisees sont `status`, `heartbeat` et `get_demo_log`.
- Les ecoutes sont limitees a `127.0.0.1`.
- Les donnees de secrets, de keylogging et de persistance sont synthetiques.
- Les tests automatises et le scenario de demonstration constituent les preuves du comportement implemente.
- Les fonctions offensives du sujet sont documentees pour la detection, mais ne sont pas executees par ce depot.

## Sources

- MITRE ATT&CK, Enterprise : https://attack.mitre.org/
- Tactique Command and Control : https://attack.mitre.org/tactics/TA0011/
- C2Lab, laboratoire pedagogique : https://c2lab.xyz/
- Stéphane Robert, Command & Control : https://blog.stephane-robert.info/docs/securiser/menaces/phases/command-control/
