"""MCP server for detailed Cetelem France credit simulations."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field

API_KEY = os.getenv("CETELEM_API_KEY", "")
API_BASE_URL = os.getenv(
    "CETELEM_API_BASE_URL",
    "https://api-fr.bnpparibas-pf.com/fr/loansimulation_b2c/v1",
).rstrip("/")
DEFAULT_VENDOR_CODE = os.getenv("CETELEM_VENDOR_CODE", "1001989870")
DEFAULT_MATERIAL_CODE = os.getenv("CETELEM_MATERIAL_CODE", "330")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

MATERIAL_CODES = {
    "travaux éco-responsables": "115",
    "décoration": "330",
    "véhicule essence/diesel/autre neuf": "501",
    "véhicule essence/diesel/autre occasion": "502",
    "véhicule électrique neuf": "509",
    "véhicule électrique occasion": "510",
    "caravane/camping-car neuf": "520",
    "caravane/camping-car occasion": "521",
    "hybride rechargeable neuf": "530",
    "hybride rechargeable occasion": "531",
    "vacances et loisirs": "660",
    "événements de vie": "676",
    "santé et bien-être": "680",
    "autres travaux": "919",
}

mcp = FastMCP(
    "Cetelem Simulation",
    instructions=(
        "Les outils disponibles retournent uniquement des offres détaillées "
        "pour un montant et une durée précis. Ils ne calculent pas de mensualité "
        "cible et ne recherchent pas de durées possibles. Les résultats sont "
        "indicatifs et ne constituent ni une offre ferme ni une décision "
        "d’éligibilité. Utilise simulate_pp_detail pour un prêt personnel et "
        "simulate_cr_detail pour un crédit renouvelable."
    ),
    host=HOST,
    port=PORT,
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


def resolve_material_code(code: str) -> str:
    if code.isdigit():
        return code
    normalized = code.lower().strip()
    return MATERIAL_CODES.get(normalized, code)


async def call_cetelem_api(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not API_KEY:
        return {"error": "Configuration manquante : définissez CETELEM_API_KEY."}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.cetelem.fr",
        "Referer": "https://www.cetelem.fr/",
        "Content-Type": "application/json",
        "apikey": API_KEY,
        "sec-ch-ua": '"Not:A-Brand";v="8", "Chromium";v="156", "Google Chrome";v="156"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/{endpoint}",
                headers=headers,
                json=payload,
            )
    except httpx.HTTPError as exc:
        return {"error": f"Échec de connexion à l’API Cetelem : {exc}"}

    try:
        data = response.json()
    except json.JSONDecodeError:
        data = {"rawResponse": response.text[:2000]}

    if not response.is_success:
        return {
            "error": f"L’API Cetelem a répondu HTTP {response.status_code}.",
            "details": data,
        }
    return data


@mcp.tool()
async def simulate_pp_detail(
    amount: float = Field(gt=0, description="Montant exact du prêt personnel en euros"),
    duration: int = Field(gt=0, description="Durée exacte du prêt en mois"),
    material_code: str = Field(
        default=DEFAULT_MATERIAL_CODE,
        description=(
            "Code numérique du projet ou nom connu, par exemple 330 ou décoration."
        ),
    ),
    vendor_code: str = Field(
        default=DEFAULT_VENDOR_CODE,
        description="Code vendeur Cetelem (1001989870 par défaut).",
    ),
) -> dict[str, Any]:
    """Retourne l’offre détaillée d’un prêt personnel pour un montant et une durée précis.

    Projets disponibles pour material_code : 115 travaux éco-responsables ;
    330 décoration ; 501 véhicule essence/diesel/autre neuf ;
    502 véhicule essence/diesel/autre occasion ; 509 véhicule électrique neuf ;
    510 véhicule électrique occasion ; 520 caravane/camping-car neuf ;
    521 caravane/camping-car occasion ; 530 hybride rechargeable neuf ;
    531 hybride rechargeable occasion ; 660 vacances et loisirs ;
    676 événements de vie ; 680 santé et bien-être ; 919 autres travaux.
    Le code 810 correspond aux imprévus ; le test à 72 mois a été refusé
    car la durée dépasse la limite de ce projet. Les noms de projets peuvent
    être fournis à la place des codes. Les résultats dépendent du montant et
    de la durée sélectionnés.
    """
    payload = {
        "materialCode": resolve_material_code(material_code),
        "simulations": {
            "0": {"amount": amount, "duration": duration, "irregularDuration1": 0}
        },
        "vendorCode": vendor_code,
    }
    return await call_cetelem_api("detail-simulations-pp", payload)


@mcp.tool()
async def simulate_cr_detail(
    amount: float = Field(
        gt=0, description="Montant exact du crédit renouvelable en euros"
    ),
    duration: int = Field(gt=0, description="Durée exacte du crédit en mois"),
    vendor_code: str = Field(
        default=DEFAULT_VENDOR_CODE,
        description="Code vendeur Cetelem (1001989870 par défaut).",
    ),
) -> dict[str, Any]:
    """Retourne l’offre détaillée d’un crédit renouvelable pour un montant et une durée précis."""
    payload = {
        "simulations": {
            "0": {"amount": amount, "duration": duration, "productType": "EMI"}
        },
        "vendorCode": vendor_code,
    }
    return await call_cetelem_api("detail-simulation-cr", payload)


if __name__ == "__main__":
    mcp.run(transport=MCP_TRANSPORT)

