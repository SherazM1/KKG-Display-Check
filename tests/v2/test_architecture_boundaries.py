"""Portable backend boundaries before HTTP exposure.

Future API validation must reject incorrect external types (including boolean
quantities), enforce intake allowlists, and construct one ProjectContext.
ResolvedDisplay, DisplayKnowledgeProfile, and EstimateBasis must be derived
internally, never accepted as authoritative client inputs. The basis builder's
knowledge/display identity guards are covered in test_estimate_basis.py.

Readiness is intake completeness, not an external request schema. The tests
below characterize its current permissiveness, not acceptable API payloads.
"""

from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from app.v2.models import ProjectContext, ProjectDimensions, is_project_ready
from app.v2.services.display_resolver import resolve_display
from app.v2.services.display_knowledge_service import resolve_display_knowledge
from app.v2.services.estimate_basis_service import build_estimate_basis


PORTABLE_MODULES = (
    "app.v2.models",
    "app.v2.display_registry",
    "app.v2.intake_options",
    "app.v2.uploads",
    "app.v2.knowledge.display_profiles",
    "app.v2.services.display_resolver",
    "app.v2.services.display_knowledge_service",
    "app.v2.services.estimate_basis_service",
)


@pytest.mark.parametrize(
    "forbidden",
    [
        ("streamlit",),
        ("app.catalog", "app.pricing", "app.gallery", "app.visualizer"),
        ("api",),
    ],
    ids=["no-streamlit", "no-v1-application-modules", "no-api-dependency"],
)
def test_portable_backend_imports_and_runs_without_forbidden_modules(forbidden) -> None:
    """Fresh interpreter catches transitive and lazy imports despite pytest caches."""
    script = textwrap.dedent(
        """
        import importlib
        import importlib.abc
        import json
        import sys

        root, module_json, forbidden_json = sys.argv[1:]
        sys.path.insert(0, root)
        forbidden = tuple(json.loads(forbidden_json))

        def blocked(name):
            return any(name == item or name.startswith(item + '.') for item in forbidden)

        assert not any(blocked(name) for name in sys.modules)
        attempts = []

        class ImportGuard(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if blocked(fullname):
                    attempts.append(fullname)
                    raise ImportError('Forbidden backend dependency: ' + fullname)
                return None

        sys.meta_path.insert(0, ImportGuard())
        for name in json.loads(module_json):
            importlib.import_module(name)

        from app.v2.models import ProjectContext, is_project_ready
        from app.v2.services.display_resolver import resolve_display
        from app.v2.services.display_knowledge_service import resolve_display_knowledge
        from app.v2.services.estimate_basis_service import build_estimate_basis
        from app.v2.uploads import sanitize_image_upload
        from io import BytesIO
        from PIL import Image

        project = ProjectContext()
        assert is_project_ready(project)
        display = resolve_display(project)
        knowledge = resolve_display_knowledge(display)
        assert build_estimate_basis(project, display, knowledge).review_required
        buffer = BytesIO()
        Image.new('RGB', (2, 2)).save(buffer, format='PNG')
        assert sanitize_image_upload(
            image_bytes=buffer.getvalue(), filename='reference.png', mime_type='image/png'
        ).mime_type == 'image/png'

        # Also catch optional imports whose ImportError was swallowed.
        assert not attempts, attempts
        assert not any(blocked(name) for name in sys.modules)
        """
    )
    result = subprocess.run(
        [
            sys.executable, "-I", "-B", "-c", script,
            str(Path(__file__).resolve().parents[2]),
            json.dumps(PORTABLE_MODULES), json.dumps(forbidden),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_one_project_drives_deterministic_workflow_and_json_compatible_outputs() -> None:
    """API adapters must derive these outputs from one validated request."""
    project = ProjectContext(
        display_family="sidekick",
        display_configuration="hooks",
        baseline_size="48",
        footprint_id="sk-48-hooks",
        quantity=725,
        print_type="Digital Print",
        shipping_packout="Assembled",
        dimensions=ProjectDimensions(width=46.5, height=52.25, depth=13.75),
    )
    original = asdict(project)

    def run_workflow():
        assert is_project_ready(project)
        display = resolve_display(project)
        knowledge = resolve_display_knowledge(display)
        basis = build_estimate_basis(project, display, knowledge)
        return display, knowledge, basis

    display, knowledge, basis = run_workflow()
    assert (display, knowledge, basis) == run_workflow()
    assert asdict(project) == original
    assert display.family_id == knowledge.family_id == basis.family_id == project.display_family
    assert (
        display.configuration_id == knowledge.configuration_id
        == basis.configuration_id == project.display_configuration
    )
    assert display.baseline_id == basis.baseline_id == project.baseline_size
    assert knowledge.baseline_id is None  # Seeded configuration-wide Hooks profile.
    assert knowledge.profile_id == "sidekick/hooks"
    assert display.footprint_id == basis.footprint_id == project.footprint_id
    assert (basis.quantity, basis.print_type, basis.shipping_packout) == (
        project.quantity, project.print_type, project.shipping_packout
    )
    assert (display.width, display.height, display.depth) == (
        basis.width, basis.height, basis.depth
    ) == (project.dimensions.width, project.dimensions.height, project.dimensions.depth)
    assert display.units == basis.units == "in"
    assert basis.unknowns == knowledge.known_unknowns
    assert basis.unknowns
    assert basis.review_required is True
    assert basis.review_reasons == (
        "Display knowledge contains unresolved technical unknowns.",
    )

    # Adapter feasibility only: no serialization methods belong in the domain.
    for output in (display, knowledge, basis):
        payload = json.loads(json.dumps(asdict(output), allow_nan=False))
        assert payload["family_id"] == project.display_family
    assert payload["unknowns"] == list(knowledge.known_unknowns)


@pytest.mark.parametrize("quantity", [-1, 0, 1, 725])
def test_quantity_readiness_enforces_minimum(quantity: int) -> None:
    assert is_project_ready(ProjectContext(quantity=quantity)) is (quantity >= 1)


@pytest.mark.parametrize("quantity", [True, 1.0, 1.5])
def test_external_quantity_type_validation_is_deferred_to_api(quantity) -> None:
    """Python permits these values; future API must require a non-bool integer."""
    project = ProjectContext(quantity=quantity)
    assert is_project_ready(project)
    assert type(project.quantity) is type(quantity)  # Dataclass does not coerce.


@pytest.mark.parametrize("field", ["print_type", "shipping_packout"])
@pytest.mark.parametrize("value", ["", " \t", "unsupported-external-value"])
def test_intake_text_completeness_is_separate_from_api_allowlists(field, value) -> None:
    """API must validate membership; readiness only checks nonempty text."""
    assert is_project_ready(ProjectContext(**{field: value})) is bool(value.strip())
