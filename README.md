# Cetelem Simulation MCP (Python)

Serveur MCP Python qui expose l’outil `cetelem_simulate` pour comparer jusqu’à dix simulations de prêt personnel Cetelem France.

## Ce que les essais API ont montré

Avec le vendeur `1001989870` et le produit `330` :

- `POST /detail-simulations-pp` accepte plusieurs entrées numérotées dans `simulations` et renvoie les offres dans le même ordre.
- Une simulation fonctionne avec `amount` et `duration`. `irregularDuration1` est facultatif ; l’omission et la valeur `0` ont donné le même résultat testé.
- Les durées testées (12, 36, 72 et 84 mois) sont acceptées. À 12 mois, l’API a renvoyé `differentialOffer: true` avec `tncMin` et `tncMax`; les autres durées testées renvoyaient `tncFixed`.
- Les codes vendeur ou produit inconnus testés ont renvoyé HTTP 400.
- Exemple vérifié : 10 000 € sur 72 mois retourne 176,51 €/mois hors assurance, 185,35 €/mois avec assurance, 8,56 % de TAEG, 2 708,72 € d’intérêts et 12 708,72 € dus hors assurance.

Les essais ne déterminent pas toutes les limites de montant/durée ni l’ensemble des codes acceptés. Les conditions sont fournies par l’API et peuvent évoluer.

## Codes matériau trouvés

Le simulateur public contient un catalogue hiérarchique de projets. L’API attend un code numérique correspondant au projet final sélectionné, pas nécessairement le code de la catégorie parente.

Codes testés avec `vendorCode=1001989870`, `amount=10000` et `duration=72` :

| Projet final | `materialCode` | Résultat |
|---|---:|---|
| Travaux éco-responsables | `115` | Accepté, offre différentielle |
| Décoration | `330` | Accepté |
| Véhicule essence/diesel/autre neuf | `501` | Accepté |
| Véhicule essence/diesel/autre occasion | `502` | Accepté |
| Véhicule électrique neuf | `509` | Accepté, offre différentielle |
| Véhicule électrique occasion | `510` | Accepté, offre différentielle |
| Caravane/camping-car neuf | `520` | Accepté |
| Caravane/camping-car occasion | `521` | Accepté |
| Hybride rechargeable neuf | `530` | Accepté, offre différentielle |
| Hybride rechargeable occasion | `531` | Accepté, offre différentielle |
| Vacances et loisirs | `660` | Accepté |
| Événements de vie | `676` | Accepté |
| Santé et bien-être | `680` | Accepté |
| Autres travaux | `919` | Accepté |

Le code `810` (« Imprévus ») figure dans le catalogue, mais la durée testée de 72 mois dépasse la durée maximale acceptée pour ce projet. Les codes `503`, `504` et `5044` correspondent à des choix intermédiaires du catalogue et n’ont pas donné de simulation exploitable. Le code par défaut `805` a répondu « Aucun barème trouvé » pour le test 10 000 €/72 mois.

## Démarrer en local

Python 3.10 ou plus récent :

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:CETELEM_API_KEY="votre-clé API"
python server.py
```

Le serveur MCP Streamable HTTP écoute sur `http://localhost:8000/mcp`. Pour le lancer en STDIO avec un client local :

```powershell
$env:MCP_TRANSPORT="stdio"
python server.py
```

## Brancher à ChatGPT

ChatGPT doit joindre un endpoint MCP Streamable HTTP public en HTTPS. Déployez le serveur sur un hébergeur Python ou avec Docker, configurez `CETELEM_API_KEY` comme secret d’environnement et ajoutez l’URL publique finissant par `/mcp` à une app/serveur MCP personnalisé dans ChatGPT Web. Utilisez **Scan Tools** pour découvrir `cetelem_simulate`. La création d’apps personnalisées dépend de l’offre et des paramètres du compte ou de l’espace de travail.

Ne rendez pas publique la clé API. Pour un serveur partagé, ajoutez une authentification OAuth compatible ChatGPT ou limitez l’accès au niveau de l’hébergeur/proxy. ChatGPT ne prend pas en charge une clé API personnalisée comme authentification MCP directe.

## Paramètres

- `CETELEM_API_KEY` : clé requise pour appeler l’API.
- `CETELEM_VENDOR_CODE` : vendeur par défaut (`1001989870`).
- `CETELEM_MATERIAL_CODE` : produit par défaut (`330`).
- `CETELEM_API_BASE_URL` : URL API alternative pour diagnostic.
- `HOST` et `PORT` : écoute HTTP (`0.0.0.0:8000` par défaut).
- `MCP_TRANSPORT=stdio` : sélectionne STDIO ; par défaut, le transport est Streamable HTTP.

`cetelem_simulate` prend une liste `scenarios` de 1 à 10 objets `{ "amount": 10000, "duration": 72 }`. Chaque objet accepte aussi `irregularDuration1` (0 par défaut). Les champs `vendor_code` et `material_code` sont optionnels.

Les résultats sont indicatifs, pas une offre de crédit ni une décision d’éligibilité.
