"""MCP server for indicative Cetelem France loan simulations."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

API_KEY = os.getenv("CETELEM_API_KEY", "")
API_BASE_URL = os.getenv(
    "CETELEM_API_BASE_URL",
    "https://api-fr.bnpparibas-pf.com/fr/loansimulation_b2c/v1",
).rstrip("/")
DEFAULT_VENDOR_CODE = os.getenv("CETELEM_VENDOR_CODE", "1001989870")
DEFAULT_MATERIAL_CODE = os.getenv("CETELEM_MATERIAL_CODE", "330")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


class Scenario(BaseModel):
    amount: float = Field(gt=0, description="Montant emprunté en euros")
    duration: int = Field(gt=0, description="Durée en mois")
    irregularDuration1: int = Field(
        default=0, ge=0,
        description="Durée irrégulière éventuelle en mois (0 par défaut)",
    )


mcp = FastMCP(
    "Cetelem Simulation",
    instructions=(
        "Simule des prêts personnels Cetelem France. Les résultats sont indicatifs, "
        "et ne constituent ni une offre de crédit ni une décision d’éligibilité."
    ),
    host=HOST,
    port=PORT,
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
async def cetelem_simulate(
    scenarios: list[Scenario] = Field(
        min_length=1, max_length=10,
        description="1 à 10 scénarios montant/durée à comparer.",
    ),
    vendor_code: str = Field(
        default=DEFAULT_VENDOR_CODE,
        description="Code vendeur Cetelem (1001989870 par défaut).",
    ),
    material_code: str = Field(
        default=DEFAULT_MATERIAL_CODE,
        description="Code produit Cetelem (330 par défaut).",
    ),
) -> dict[str, Any]:
    """Compare un ou plusieurs scénarios de prêt personnel Cetelem."""
    if not API_KEY:
        return {"error": "Configuration manquante : définissez CETELEM_API_KEY sur le serveur."}

    payload = {
        "vendorCode": vendor_code,
        "materialCode": material_code,
        "simulations": {
            str(index): scenario.model_dump()
            for index, scenario in enumerate(scenarios)
        },
    }
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
                f"{API_BASE_URL}/detail-simulations-pp",
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
            "hint": "Vérifiez les codes vendeur/produit et les paramètres de simulation.",
        }
    return data


if __name__ == "__main__":
    if os.getenv("MCP_TRANSPORT", "streamable-http") == "stdio":
        mcp.run()
    else:
        mcp.run(transport="streamable-http")
