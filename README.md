# Agri-Conseil API

API Django REST Framework pour le suivi des cultures agricoles au Sénégal.

## Prévision indicative avant récolte

`GET /api/mes-cultures/{id}/prevision-rendement/` renvoie, pour une culture appartenant à l'utilisateur authentifié, les caractéristiques agronomiques enregistrées, le stade si calculable, la période de récolte indicative si le référentiel annuel est validé et complet, la météo disponible, les opérations futures issues des règles du calendrier et les limites de chaque calcul. L'endpoint utilise le service de calendrier existant pour créer ou actualiser son calendrier, sans supprimer les opérations déjà enregistrées.

Le rendement estimé et la quantité totale restent `null` tant qu'une référence de rendement vérifiée et adaptée à la culture et à la zone n'existe pas. La superficie n'a pas d'unité définie dans le modèle actuel. Les cultures pérennes n'ont pas de champ décrivant leur période de fructification/récolte ; aucune date n'est donc inventée pour elles.

Exemple de réponse lorsque le référentiel manque (les données météo et les dates sont ici indisponibles) :

```json
{
  "culture_suivie_id": 12,
  "culture": "Riz",
  "statut": "rendement_indisponible",
  "methode": "Aucune estimation chiffrée : les données de rendement vérifiées sont absentes.",
  "superficie": "2.50",
  "unite_superficie": null,
  "date_semis": "2026-06-01",
  "type_cycle": null,
  "caracteristiques_agronomiques": null,
  "stade_actuel": null,
  "recolte_prevue": {
    "date_debut": null,
    "date_fin": null,
    "statut": "indisponible",
    "raison_indisponible": "Aucun référentiel agronomique n'est associé à cette culture.",
    "source": null
  },
  "rendement_estime_kg_ha": null,
  "quantite_totale_estimee_kg": null,
  "meteo": null,
  "risques": {
    "meteorologique": {
      "statut": "indisponible",
      "raison": "Le service météo est indisponible pour le moment."
    },
    "hydrique": {
      "statut": "indisponible",
      "raison": "ETo, ETc et déficit hydrique ne sont pas calculés par le module actuel."
    }
  },
  "facteurs_favorables": [],
  "facteurs_defavorables": [],
  "recommandations": [],
  "references": [],
  "calcule_le": "2026-10-14T10:00:00Z",
  "limites": [
    "Aucune référence de rendement validée et adaptée à cette culture et à cette zone n'est disponible.",
    "Le modèle ne relie pas les régions administratives aux zones agroécologiques ; l'adaptation géographique ne peut pas être vérifiée automatiquement.",
    "La superficie du modèle n'a pas d'unité explicite ; aucune quantité totale ne peut être calculée.",
    "Le module hydrique ne calcule actuellement ni ETo, ni ETc, ni déficit hydrique."
  ],
  "donnees_manquantes": [
    "Aucun référentiel agronomique n'est associé à cette culture.",
    "Référentiel agronomique absent.",
    "Cycle de récolte vérifié et identifiable.",
    "Référence de rendement vérifiée et adaptée à la culture et à la zone.",
    "Correspondance vérifiée entre la région de la parcelle et la zone agroécologique de la référence.",
    "Unité de superficie de la parcelle.",
    "Calcul hydrique validé (ETo, ETc et déficit hydrique)."
  ]
}
```

L'exemple de date de calcul est illustratif. La météo est obtenue auprès du service OpenWeather existant. En cas d'indisponibilité, le champ météo est `null` et le statut météo l'indique. Les conseils météo ne sont repris que si le fournisseur a retourné des points de prévision pour la journée. Les facteurs restent vides tant qu'aucun seuil de risque validé n'est configuré.

Les endpoints exigent `Authorization: Token <token>`. Une culture inexistante ou appartenant à un autre compte renvoie `404`; une requête sans authentification est refusée. La prévision de rendement reste indisponible tant qu'une référence de rendement vérifiée et adaptée à la zone n'est pas fournie.

### Analyse qualitative optionnelle avec Gemini

La réponse de prévision peut contenir un bloc additionnel `analyse_ia` avec un résumé, des facteurs et des recommandations qualitatives. Ce bloc reste `indisponible` si `GEMINI_API_KEY` est absente, si le fournisseur échoue ou si sa réponse ne passe pas la validation. Les champs déterministes de prévision et les listes `recommandations` existantes ne sont pas remplacés.

Gemini ne fournit pas de rendement chiffré dans l'intégration actuelle : le modèle ne contient pas de référence de rendement validée et l'unité de superficie n'est pas définie. Pour activer l'analyse qualitative, définir `GEMINI_API_KEY` dans l'environnement du backend. `GEMINI_MODEL` est facultative et vaut `gemini-3.5-flash-lite` par défaut. Ne placez jamais la clé dans React.

## Saisie de la récolte réelle

- `GET /api/mes-cultures/{id}/recoltes-reelles/` liste les récoltes réelles de cette culture.
- `POST /api/mes-cultures/{id}/recoltes-reelles/` enregistre une récolte réelle.

Exemple de corps POST :

```json
{
  "date_recolte": "2026-10-10",
  "quantite": "125.500",
  "unite": "kg",
  "observations": "Récolte pesée"
}
```

Les unités acceptées sont `kg` et `tonne`. Seul le propriétaire de la culture suivie peut consulter ou enregistrer ses données. Les récoltes réelles sont stockées séparément des estimations.

## Calendrier

Les stades calculés sont désormais associés à une culture suivie. Les anciennes lignes de stade restent conservées avec leur relation `culture_suivie` vide. La régénération du calendrier ne supprime plus les opérations existantes et préserve leur statut.

## Références de rendement et méthode hybride

Le modèle `ReferenceRendement` conserve les valeurs publiées avec culture, variété, zone, système cultural, cycle, classes d'âge des arbres, unité, période, conditions de mesure et source. Les lignes importées sont toujours `valide=False` et doivent être relues dans l'administration avant validation. La base de ce workspace ne contenait aucune référence ni aucun catalogue `CultureRef` au moment de l'audit ; le gabarit ne fournit que les codes attendus et aucune valeur de rendement.

Compléter `apps/cultures/data/references_rendement_template.csv` uniquement avec des valeurs reprises de sources documentées. Les codes `mil`, `arachide`, `riz`, `mais`, `sorgho`, `niebe`, `manioc`, `oignon`, `mangue` et `pasteque` doivent d'abord exister dans `CultureRef`. Lancer la validation sans écriture :

```powershell
python manage.py import_references_rendement --csv apps/cultures/data/references_rendement_template.csv --dry-run
```

Après revue du fichier, l'import effectif utilise la même commande sans `--dry-run`. Elle refuse le fichier entier en cas d'erreur ou de doublon. L'import ne valide jamais les lignes. Une référence géographique spécifique reste inutilisable pour une parcelle tant qu'une correspondance administrative vers la zone agroécologique n'est pas établie.

La réponse distingue `rendement_reference` des champs `rendement_estime_kg_ha` et `quantite_totale_estimee_kg`. Ces derniers restent `null` : aucune méthode d'ajustement agronomique documentée n'est implémentée. Les récoltes réelles restent des observations séparées et n'entraînent pas automatiquement une prédiction.

Les migrations `calendrier.0005`, `cultures.0006` et `cultures.0007` ajoutent respectivement l'association de stade par culture suivie, le modèle des récoltes réelles, puis les dimensions de parcelle et les références de rendement. Elles ne suppriment pas les stades existants et n'insèrent aucune référence agronomique.

## Installation et vérifications

### Recherche de documents agronomiques (collecte manuelle, à la demande)

La collecte n'utilise aucun moteur ou abonnement de recherche. Un administrateur peut importer un PDF depuis son ordinateur dans `/admin/`, ou enregistrer l'URL exacte d'un document public officiel. Les pages [publications DAPSA](https://www.dapsa.gouv.sn/toutes-les-publications), [ISRA](https://isra.sn/) et [FAO](https://www.fao.org/) peuvent être conservées; pour l'extraction automatique, copiez l'URL directe du PDF ou de la page qui contient les données agronomiques. L'application ne parcourt pas ces portails pour découvrir les documents.

La clé Gemini est facultative et reste uniquement côté backend. Pour activer l'extraction, créez une clé dans [Google AI Studio](https://aistudio.google.com/app/apikey) et renseignez `GEMINI_API_KEY` dans le `.env` du backend. Sans cette clé, l'administrateur peut toujours importer, lier et enregistrer les documents; les champs agronomiques restent à compléter ou extraire ultérieurement.

```powershell
python manage.py migrate
python manage.py collect_references_agronomiques --culture riz --url "https://isra.sn/chemin/vers/guide-riz.pdf" --title "Guide riz"
python manage.py collect_references_agronomiques --culture riz --url "https://www.fao.org/chemin/vers/document.pdf" --extract
```

La commande ci-dessus enregistre une URL directe sans contacter le site. L'option `--extract` tente ensuite de lire un PDF ou une page HTML depuis les domaines HTTPS officiels autorisés (ISRA, DAPSA, FAO, AfricaRice), sans contourner leurs protections. Le téléchargement est limité à 8 Mo, utilise des délais d'attente et vérifie les redirections. Dans l'administration, l'action « Extraire les champs avec Gemini » permet aussi de traiter un PDF importé. Les preuves et pages extraites sont conservées; les champs absents restent vides. Si Gemini manque ou échoue, le document reste enregistré et en attente de revue.

Après `python manage.py migrate`, connectez-vous à `/admin/` avec un compte administrateur. Créez une référence, choisissez sa culture et joignez un PDF (8 Mo maximum) ou saisissez une URL HTTPS officielle. Enregistrez d'abord le formulaire; l'action « Extraire les champs avec Gemini » est facultative. Examinez ensuite le fichier ou ouvrez le lien, vérifiez les valeurs et les preuves, puis utilisez « Valider les références sélectionnées » ou « Rejeter les références sélectionnées ». Toute référence importée commence avec le statut `A_VERIFIER`; seules les références validées servent aux calculs. Un lien documentaire identique pour la même culture n'est pas enregistré deux fois.

Les fichiers sont conservés dans le stockage média local configuré par Django (`MEDIA_ROOT`). En production, configurez la sauvegarde et la distribution protégée de ce répertoire; ne rendez pas les documents privés accessibles publiquement par défaut.

L'extraction automatique ne valide pas l'exactitude scientifique des réponses Gemini : les preuves doivent toujours être vérifiées par une personne. Les sites qui bloquent le téléchargement ou dont le format n'est pas pris en charge restent des candidats à examiner manuellement. Une correspondance validée entre chaque région administrative et les zones agroécologiques reste à construire.

Après l'enregistrement, le tableau de bord React charge l'endpoint privé de prévision. Il montre le rendement et la production de référence séparément de la prévision réelle. Les champs de prévision restent vides tant qu'aucune méthode d'ajustement agronomique documentée n'est disponible. Le formulaire enregistre l'unité hectares et permet de préciser variété et système cultural.

```powershell
python manage.py migrate
python manage.py test apps.cultures.tests apps.calendrier.tests
```

Les tests météo utilisent des mocks ; ils ne nécessitent pas d'appel réel à OpenWeather.
