# Strasbourg Parkings

Intégration Home Assistant pour suivre les places disponibles dans les parkings
publics de l'Eurométropole de Strasbourg.

> Projet communautaire non affilié à l'Eurométropole de Strasbourg. Les données
> sont publiées par son portail Open Data officiel.

## Fonctionnalités

- Sélection des parkings à suivre pendant la configuration, sans compte ni clé
  API.
- Capteur **Places disponibles** avec le nombre de places libres, la capacité,
  le taux d'occupation et l'état temps réel.
- Capteur binaire **Ouvert** pour les automatisations et les tableaux de bord.
- Une seule requête partagée pour tous les parkings sélectionnés.
- Actualisation configurable de 3 à 15 minutes ; trois minutes est le minimum,
  car c'est la cadence annoncée par la source.

## Installation avec HACS

Tant que le dépôt n'est pas dans le catalogue HACS par défaut :

1. Dans HACS, ouvrez **Intégrations**, puis le menu ⋮ et choisissez
   **Dépôts personnalisés**.
2. Ajoutez `https://github.com/hehrstein/strasbourg-parkings` avec la catégorie
   **Integration**.
3. Installez **Strasbourg Parkings** puis redémarrez Home Assistant.
4. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration**,
   recherchez **Strasbourg Parkings**, puis choisissez vos parkings.

L'intégration n'utilise ni compte, ni mot de passe, ni jeton : les données sont
publiques.

## Entités créées

Chaque parking sélectionné devient un appareil Home Assistant contenant :

- `Places disponibles` : nombre de places libres ;
- `Ouvert` : état ouvert ou fermé.

Le capteur de places expose également les attributs suivants :

| Attribut | Signification |
| --- | --- |
| `total_capacity` | Capacité totale communiquée par la source |
| `occupancy_percentage` | Taux d'occupation calculé ou fourni par la source |
| `status` | Libellé d'état, par exemple `Ouvert` ou `Fermé` |
| `realtime_status` | Code de statut temps réel de la source |
| `latitude`, `longitude` | Position publiée du parking |
| `data_updated_at` | Moment de la dernière réponse Open Data reçue |

Exemple d'automatisation pour une alerte de saturation :

```yaml
alias: Alerte parking Rivetoile bientôt complet
triggers:
  - trigger: numeric_state
    entity_id: sensor.strasbourg_parking_rivetoile_places_disponibles
    below: 50
conditions:
  - condition: state
    entity_id: binary_sensor.strasbourg_parking_rivetoile_ouvert
    state: "on"
actions:
  - action: notify.mobile_app_mon_telephone
    data:
      message: "Rivetoile a moins de 50 places libres."
mode: single
```

Adaptez les identifiants d'entité à ceux créés dans votre installation.

## Source et fraîcheur des données

La source est le jeu officiel
[Occupation en temps réel des parkings](https://data.strasbourg.eu/explore/dataset/occupation-parkings-temps-reel/information/)
de l'Eurométropole de Strasbourg. Il fournit les places libres, la capacité et
l'état des parkings et annonce une actualisation toutes les trois minutes.

L'intégration ne réinterroge donc jamais l'API à une cadence inférieure à trois
minutes. Elle affiche l'heure locale de récupération dans l'attribut
`data_updated_at`; cette heure indique la fraîcheur de la réponse reçue, et ne
prétend pas être l'heure de mesure des capteurs physiques du parking.

## Développement

```bash
python -m pip install -r requirements_test.txt
pytest
```

La suite couvre le parsing de la source, la sélection des parkings, les erreurs
de connexion dans le flux d'options et les traductions de secours en anglais.

## Licence

Le code est distribué sous [licence MIT](LICENSE). Cette licence ne couvre pas
les données : leur réutilisation reste soumise aux conditions publiées par
l'Eurométropole de Strasbourg. Toute carte ou automatisation qui affiche les
données doit en citer la source.
