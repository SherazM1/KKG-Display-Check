"""Derive authoritative analysis objects from one validated project request."""

from dataclasses import asdict

from fastapi import APIRouter

from api.errors import ProjectNotReadyError
from api.schemas import (
    AnalysisStatus, AnalyzeRequest, AnalyzeResponse, Dimensions,
    EstimateBasisResponse, KnowledgeResponse, ProjectResponse, ResolvedDisplayResponse,
)
from app.v2.models import ProjectContext, ProjectDimensions, is_project_ready
from app.v2.services.display_resolver import resolve_display
from app.v2.services.display_knowledge_service import resolve_display_knowledge
from app.v2.services.estimate_basis_service import build_estimate_basis


router = APIRouter()


@router.post("/project/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    project = ProjectContext(
        project_name=request.project_name,
        display_family=request.display_family,
        display_configuration=request.display_configuration,
        baseline_size=request.baseline_size,
        footprint_id=request.footprint_id,
        display_type="", legacy_display_id="",
        quantity=request.quantity,
        print_type=request.print_type,
        shipping_packout=request.shipping_packout,
        dimensions=ProjectDimensions(
            width=request.dimensions.width, height=request.dimensions.height,
            depth=request.dimensions.depth,
        ),
        notes=request.notes,
    )
    # reference_image_id is reserved; no storage or domain reference is implied.
    if not is_project_ready(project):
        raise ProjectNotReadyError("Project intake is not ready.")
    display = resolve_display(project)
    knowledge = resolve_display_knowledge(display)
    basis = build_estimate_basis(project, display, knowledge)
    return AnalyzeResponse(
        status=AnalysisStatus(),
        project=ProjectResponse(
            project_name=project.project_name, quantity=project.quantity,
            print_type=project.print_type, shipping_packout=project.shipping_packout,
            dimensions=Dimensions(**asdict(project.dimensions)), notes=project.notes,
        ),
        resolved_display=ResolvedDisplayResponse.model_validate(asdict(display)),
        knowledge=KnowledgeResponse.model_validate(asdict(knowledge)),
        estimate_basis=EstimateBasisResponse.model_validate(asdict(basis)),
    )
