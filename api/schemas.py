"""Explicit external contracts; domain dataclasses remain HTTP-independent."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.v2.intake_options import PRINT_TYPE_OPTIONS, SHIPPING_PACKOUT_OPTIONS


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


PositiveDimension = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]
Quantity = Annotated[int, Field(strict=True, ge=1)]
Text = Annotated[str, Field(strict=True)]


class Dimensions(APIModel):
    width: PositiveDimension
    height: PositiveDimension
    depth: PositiveDimension
    units: Literal["in"] = "in"


class AnalyzeRequest(APIModel):
    project_name: Text = ""
    display_family: Text
    display_configuration: Text
    baseline_size: Text
    footprint_id: Text
    quantity: Quantity
    print_type: Text
    shipping_packout: Text
    dimensions: Dimensions
    notes: Text = ""
    reference_image_id: Text | None = None

    @field_validator("display_family", "display_configuration", "baseline_size", "footprint_id")
    @classmethod
    def require_nonblank_identity(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be blank")
        return value  # Do not silently repair canonical IDs.

    @field_validator("print_type")
    @classmethod
    def validate_print_type(cls, value: str) -> str:
        if value not in PRINT_TYPE_OPTIONS:
            raise ValueError("Unsupported print_type")
        return value

    @field_validator("shipping_packout")
    @classmethod
    def validate_shipping_packout(cls, value: str) -> str:
        if value not in SHIPPING_PACKOUT_OPTIONS:
            raise ValueError("Unsupported shipping_packout")
        return value


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"


class BaselineResponse(APIModel):
    id: str
    label: str
    footprint_id: str


class ConfigurationResponse(APIModel):
    id: str
    label: str
    baselines: list[BaselineResponse]


class FamilyResponse(APIModel):
    id: str
    label: str
    configurations: list[ConfigurationResponse]


class DisplaysResponse(APIModel):
    families: list[FamilyResponse]


class AnalysisStatus(APIModel):
    project_ready: Literal[True] = True
    display_resolved: Literal[True] = True
    knowledge_available: Literal[True] = True
    estimate_basis_built: Literal[True] = True


class ProjectResponse(APIModel):
    project_name: str
    quantity: Quantity
    print_type: str
    shipping_packout: str
    dimensions: Dimensions
    notes: str


class ResolvedDisplayResponse(APIModel):
    family_id: str
    family_label: str
    configuration_id: str
    configuration_label: str
    baseline_id: str
    baseline_label: str
    footprint_id: str
    width: PositiveDimension
    height: PositiveDimension
    depth: PositiveDimension
    units: Literal["in"]


class KnowledgeResponse(APIModel):
    profile_id: str
    family_id: str
    configuration_id: str
    baseline_id: str | None
    structural_traits: list[str]
    visible_components: list[str]
    hidden_support_components: list[str]
    known_materials: list[str]
    production_notes: list[str]
    known_unknowns: list[str]
    sources: list[str]


class EstimateBasisResponse(APIModel):
    family_id: str
    configuration_id: str
    baseline_id: str
    footprint_id: str
    quantity: Quantity
    print_type: str
    shipping_packout: str
    width: PositiveDimension
    height: PositiveDimension
    depth: PositiveDimension
    units: Literal["in"]
    structural_factors: list[str]
    material_factors: list[str]
    print_factors: list[str]
    production_factors: list[str]
    assembly_factors: list[str]
    packout_factors: list[str]
    quantity_factors: list[str]
    assumptions: list[str]
    unknowns: list[str]
    risk_factors: list[str]
    review_required: bool
    review_reasons: list[str]
    contributing_rules: list[str]


class AnalyzeResponse(APIModel):
    status: AnalysisStatus
    project: ProjectResponse
    resolved_display: ResolvedDisplayResponse
    knowledge: KnowledgeResponse
    estimate_basis: EstimateBasisResponse


ErrorCode = Literal[
    "INVALID_REQUEST", "PROJECT_NOT_READY", "DISPLAY_RESOLUTION_FAILED",
    "DISPLAY_KNOWLEDGE_UNAVAILABLE", "ESTIMATE_BASIS_FAILED", "INTERNAL_ERROR",
]


class ValidationIssue(APIModel):
    field: str
    message: str
    type: str


class ErrorDetail(APIModel):
    code: ErrorCode
    message: str
    field: str | None = None
    details: list[ValidationIssue] | None = None
    request_id: str


class ErrorResponse(APIModel):
    error: ErrorDetail
