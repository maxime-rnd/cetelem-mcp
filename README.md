# Cetelem Simulation MCP (Python)

Serveur MCP Python exposant uniquement les outils de simulation détaillée Cetelem France : prêt personnel et crédit renouvelable.

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

## Déploiement Render pour ChatGPT Web

Le dépôt comprend `render.yaml` pour créer un serveur HTTPS hébergé. Déploie-le avec [Render](https://render.com/deploy?repo=https://github.com/maxime-rnd/cetelem-mcp), sélectionne le plan gratuit et saisis `CETELEM_API_KEY` dans le champ secret demandé par Render. La clé est stockée dans les variables du service et n’est pas écrite dans le dépôt.

Après le déploiement, utilise l’URL HTTPS Render terminée par `/mcp` dans **ChatGPT Web → Plugins → + → Add custom MCP server**. Sélectionne **No authentication** et crée le plugin. Le serveur expose uniquement des simulations de prêt ; l’URL du serveur reste toutefois accessible publiquement à toute personne qui la connaît.

L’offre gratuite Render met le service en veille après 15 minutes sans trafic. Le réveil de la première requête prend environ une minute. Passe à une offre payante si tu veux éviter cette attente. Consulte les [limites du plan gratuit Render](https://render.com/docs/free).

Pour un serveur privé, configure OAuth compatible avec ChatGPT ou utilise un Secure MCP Tunnel hébergé dans un environnement cloud. Un tunnel lancé sur ton PC ne répondrait pas au besoin d’accès lorsque ton PC est éteint.

## Paramètres

- `CETELEM_API_KEY` : clé requise pour appeler l’API.
- `CETELEM_VENDOR_CODE` : vendeur par défaut (`1001989870`).
- `CETELEM_MATERIAL_CODE` : produit par défaut (`330`).
- `CETELEM_API_BASE_URL` : URL API alternative pour diagnostic.
- `HOST` et `PORT` : écoute HTTP (`0.0.0.0:8000` par défaut).
- `MCP_TRANSPORT=stdio` : sélectionne STDIO ; par défaut, le transport est Streamable HTTP.

Les outils détaillés sont `simulate_pp_detail` (prêt personnel, avec `amount`, `duration` et `material_code`) et `simulate_cr_detail` (crédit renouvelable, avec `amount` et `duration`). Ils retournent les conditions précises calculées par l’API Cetelem. Les endpoints de simulation simple ne sont pas exposés.

Les résultats sont indicatifs, pas une offre de crédit ni une décision d’éligibilité.
