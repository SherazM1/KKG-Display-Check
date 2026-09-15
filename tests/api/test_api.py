"""HTTP contract tests against the real portable backend and seeded knowledge."""

from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

from fastapi.testclient import TestClient
import pytest

from api.main import app
from api.routes import projects
from app.v2.display_registry import DISPLAY_FAMILIES
from app.v2.intake_options import PRINT_TYPE_OPTIONS, SHIPPING_PACKOUT_OPTIONS
from app.v2.services.estimate_basis_service import EstimateBasisError


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def project_request() -> dict:
    return {
        "project_name": "API project", "display_family": "sidekick",
        "display_configuration": "hooks", "baseline_size": "48",
        "footprint_id": "sk-48-hooks", "quantity": 725,
        "print_type": "Digital Print", "shipping_packout": "Assembled",
        "dimensions": {"width": 46.5, "height": 52.25, "depth": 13.75, "units": "in"},
        "notes": "Final dimensions override baseline dimensions.",
    }


def assert_error(response, status: int, code: str) -> dict:
    assert response.status_code == status, response.text
    assert set(response.json()) == {"error"}
    error = response.json()["error"]
    assert set(error) == {"code", "message", "field", "details", "request_id"}
    assert error["code"] == code
    assert error["message"]
    assert UUID(error["request_id"]).version == 4
    return error


def test_health(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_registry_is_exact_public_projection(client) -> None:
    response = client.get("/api/displays")
    assert response.status_code == 200
    expected = {"families": [
        {"id": f.id, "label": f.label, "configurations": [
            {"id": c.id, "label": c.label, "baselines": [
                {"id": b.id, "label": b.label, "footprint_id": b.footprint_id}
                for b in c.baselines
            ]} for c in f.configurations
        ]} for f in DISPLAY_FAMILIES
    ]}
    assert response.json() == expected  # Exact keys exclude paths/legacy internals.
    sidekick = next(f for f in response.json()["families"] if f["id"] == "sidekick")
    hooks = next(c for c in sidekick["configurations"] if c["id"] == "hooks")
    assert hooks["baselines"]
    assert "assets/" not in response.text
    assert "legacy_id" not in response.text


@pytest.mark.parametrize("baseline", ["24", "48"])
def test_analysis_matches_single_domain_workflow(client, project_request, baseline) -> None:
    project_request.update(baseline_size=baseline, footprint_id=f"sk-{baseline}-hooks")
    response = client.post("/api/project/analyze", json=project_request)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == dict.fromkeys([
        "project_ready", "display_resolved", "knowledge_available", "estimate_basis_built"
    ], True)
    assert body["project"] == {key: project_request[key] for key in (
        "project_name", "quantity", "print_type", "shipping_packout", "dimensions", "notes"
    )}
    display, knowledge, basis = (body[key] for key in (
        "resolved_display", "knowledge", "estimate_basis"
    ))
    assert display["family_id"] == knowledge["family_id"] == basis["family_id"] == "sidekick"
    assert display["configuration_id"] == knowledge["configuration_id"] == basis["configuration_id"] == "hooks"
    assert display["baseline_id"] == basis["baseline_id"] == baseline
    assert knowledge["baseline_id"] is None
    assert display["footprint_id"] == basis["footprint_id"] == project_request["footprint_id"]
    for key, value in project_request["dimensions"].items():
        assert display[key] == basis[key] == value
    for key in ("quantity", "print_type", "shipping_packout"):
        assert basis[key] == project_request[key]
    assert knowledge["known_unknowns"] == basis["unknowns"]
    assert basis["unknowns"]
    assert basis["review_required"] is True
    assert basis["review_reasons"] == ["Display knowledge contains unresolved technical unknowns."]
    assert basis["assumptions"] == []
    assert client.post("/api/project/analyze", json=project_request).json() == body


@pytest.mark.parametrize("field,value", [
    ("quantity", 0), ("quantity", -1), ("quantity", 500.0), ("quantity", 1.5),
    ("quantity", True), ("quantity", False), ("quantity", "500"), ("quantity", None),
    ("display_family", " "), ("display_configuration", ""),
    ("baseline_size", "\t"), ("footprint_id", ""),
    ("display_family", 123), ("print_type", ""), ("print_type", "unsupported"),
    ("shipping_packout", " "), ("shipping_packout", "unsupported"),
    ("project_name", 1), ("notes", False), ("reference_image_id", 123),
])
def test_invalid_fields(client, project_request, field, value) -> None:
    project_request[field] = value
    error = assert_error(client.post("/api/project/analyze", json=project_request), 400, "INVALID_REQUEST")
    assert error["field"] == f"body.{field}"


@pytest.mark.parametrize("field", [
    "display_family", "display_configuration", "baseline_size", "footprint_id",
    "quantity", "print_type", "shipping_packout", "dimensions",
])
def test_required_fields(client, project_request, field) -> None:
    del project_request[field]
    assert_error(client.post("/api/project/analyze", json=project_request), 400, "INVALID_REQUEST")


@pytest.mark.parametrize("dimension", ["width", "height", "depth"])
@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), -float("inf"), True, "20", None])
def test_invalid_dimensions(client, project_request, dimension, value) -> None:
    project_request["dimensions"][dimension] = value
    # Send raw JSON to exercise server-side NaN/Infinity rejection, not httpx's encoder.
    response = client.post("/api/project/analyze", content=json.dumps(project_request),
                           headers={"Content-Type": "application/json"})
    error = assert_error(response, 400, "INVALID_REQUEST")
    assert error["field"] == f"body.dimensions.{dimension}"
    assert "input" not in error["details"][0]


@pytest.mark.parametrize("dimension", ["width", "height", "depth"])
def test_missing_dimension(client, project_request, dimension) -> None:
    del project_request["dimensions"][dimension]
    assert_error(client.post("/api/project/analyze", json=project_request), 400, "INVALID_REQUEST")


def test_units_and_nested_extra_fields(client, project_request) -> None:
    project_request["dimensions"]["units"] = "cm"
    assert_error(client.post("/api/project/analyze", json=project_request), 400, "INVALID_REQUEST")
    project_request["dimensions"]["units"] = "in"
    project_request["dimensions"]["asset_path"] = "private/path"
    assert_error(client.post("/api/project/analyze", json=project_request), 400, "INVALID_REQUEST")


@pytest.mark.parametrize("field", [
    "resolved_display", "knowledge", "estimate_basis", "legacy_display_id",
    "display_type", "family_label", "configuration_label", "baseline_label",
])
def test_client_cannot_supply_derived_fields(client, project_request, field) -> None:
    project_request[field] = "client supplied"
    assert_error(client.post("/api/project/analyze", json=project_request), 400, "INVALID_REQUEST")


@pytest.mark.parametrize("field,value,code", [
    ("display_family", "unknown", "DISPLAY_RESOLUTION_FAILED"),
    ("display_family", " sidekick", "DISPLAY_RESOLUTION_FAILED"),
    ("display_configuration", "angled", "DISPLAY_RESOLUTION_FAILED"),
    ("baseline_size", "custom", "DISPLAY_RESOLUTION_FAILED"),
    ("footprint_id", "wrong", "DISPLAY_RESOLUTION_FAILED"),
])
def test_domain_resolution_errors(client, project_request, field, value, code) -> None:
    project_request[field] = value
    error = assert_error(client.post("/api/project/analyze", json=project_request), 422, code)
    assert error["details"] is None
    assert error["field"] is None


def test_missing_knowledge_stops_before_basis(client, project_request, monkeypatch) -> None:
    project_request.update(display_configuration="shelves_built", footprint_id="sk-48-shelves-built")
    calls = []
    monkeypatch.setattr(projects, "build_estimate_basis", lambda *args: calls.append(args))
    assert_error(client.post("/api/project/analyze", json=project_request), 422, "DISPLAY_KNOWLEDGE_UNAVAILABLE")
    assert calls == []


def test_project_not_ready_stops_before_resolution(client, project_request, monkeypatch) -> None:
    monkeypatch.setattr(projects, "is_project_ready", lambda project: False)
    calls = []
    monkeypatch.setattr(projects, "resolve_display", lambda *args: calls.append(args))
    assert_error(client.post("/api/project/analyze", json=project_request), 400, "PROJECT_NOT_READY")
    assert calls == []


@pytest.mark.parametrize("exception,status,code", [
    (EstimateBasisError("Knowledge identity mismatch."), 422, "ESTIMATE_BASIS_FAILED"),
    (RuntimeError("private implementation detail"), 500, "INTERNAL_ERROR"),
])
def test_basis_and_unexpected_errors(client, project_request, monkeypatch, exception, status, code) -> None:
    def fail(*args):
        raise exception
    monkeypatch.setattr(projects, "build_estimate_basis", fail)
    response = client.post("/api/project/analyze", json=project_request)
    assert_error(response, status, code)
    assert "private implementation detail" not in response.text
    assert "Traceback" not in response.text


def test_optional_fields_and_reserved_reference_do_not_change_analysis(client, project_request) -> None:
    del project_request["project_name"]
    del project_request["notes"]
    del project_request["dimensions"]["units"]
    project_request["dimensions"]["width"] = 20  # Integer physical dimensions are numbers.
    original = client.post("/api/project/analyze", json=project_request)
    assert original.status_code == 200
    assert original.json()["project"]["project_name"] == ""
    assert original.json()["project"]["notes"] == ""
    assert original.json()["project"]["dimensions"]["units"] == "in"
    for value in (None, "reserved-reference"):
        project_request["reference_image_id"] = value
        assert client.post("/api/project/analyze", json=project_request).json() == original.json()


@pytest.mark.parametrize("print_type", PRINT_TYPE_OPTIONS)
@pytest.mark.parametrize("packout", SHIPPING_PACKOUT_OPTIONS)
def test_all_shared_intake_choices_are_accepted(client, project_request, print_type, packout) -> None:
    project_request.update(print_type=print_type, shipping_packout=packout)
    assert client.post("/api/project/analyze", json=project_request).status_code == 200


def test_malformed_json_and_unique_error_ids(client) -> None:
    ids = []
    for _ in range(2):
        error = assert_error(client.post("/api/project/analyze", content="{",
                             headers={"Content-Type": "application/json"}), 400, "INVALID_REQUEST")
        ids.append(error["request_id"])
    assert ids[0] != ids[1]


def test_route_uses_same_project_and_derived_objects(client, project_request, monkeypatch) -> None:
    calls = []
    originals = {name: getattr(projects, name) for name in (
        "is_project_ready", "resolve_display", "resolve_display_knowledge", "build_estimate_basis"
    )}
    def record(name):
        def call(*args):
            result = originals[name](*args)
            calls.append((name, args, result))
            return result
        return call
    for name in originals:
        monkeypatch.setattr(projects, name, record(name))
    response = client.post("/api/project/analyze", json=project_request)
    assert response.status_code == 200
    assert [call[0] for call in calls] == list(originals)
    project = calls[0][1][0]
    assert calls[1][1][0] is project
    assert calls[2][1][0] is calls[1][2]
    basis_args = calls[3][1]
    assert basis_args[0] is project
    assert basis_args[1] is calls[1][2]
    assert basis_args[2] is calls[2][2]
    assert response.json()["estimate_basis"] == json.loads(json.dumps(asdict(calls[3][2])))


def test_api_has_no_ui_legacy_or_mock_imports() -> None:
    script = '''
import importlib.abc
import sys
sys.path.insert(0, sys.argv[1])
forbidden = ('streamlit', 'app.catalog', 'app.pricing', 'app.gallery', 'app.visualizer',
             'app.v2.mock_data', 'app.v2.services.estimate_service', 'app.v2.services.visual_service')
attempts = []
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == name or fullname.startswith(name + '.') for name in forbidden):
            attempts.append(fullname)
            raise ImportError(fullname)
sys.meta_path.insert(0, Guard())
from api.main import app
app.openapi()
assert not attempts, attempts
assert not any(name in sys.modules for name in forbidden)
'''
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script, str(Path(__file__).resolve().parents[2])],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_openapi_documents_project_error_envelope(client) -> None:
    spec = client.get("/openapi.json").json()
    responses = spec["paths"]["/api/project/analyze"]["post"]["responses"]
    for status in ("400", "422", "500"):
        assert responses[status]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorResponse"
        }
