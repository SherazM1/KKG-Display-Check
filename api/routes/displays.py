"""Browser-safe projection of the authoritative display registry."""

from fastapi import APIRouter

from api.schemas import BaselineResponse, ConfigurationResponse, DisplaysResponse, FamilyResponse
from app.v2.display_registry import DISPLAY_FAMILIES


router = APIRouter()


@router.get("/displays", response_model=DisplaysResponse)
def displays() -> DisplaysResponse:
    return DisplaysResponse(families=[
        FamilyResponse(id=family.id, label=family.label, configurations=[
            ConfigurationResponse(id=config.id, label=config.label, baselines=[
                BaselineResponse(id=baseline.id, label=baseline.label, footprint_id=baseline.footprint_id)
                for baseline in config.baselines
            ]) for config in family.configurations
        ]) for family in DISPLAY_FAMILIES
    ])
