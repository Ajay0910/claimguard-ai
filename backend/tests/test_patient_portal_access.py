import asyncio
import io
import hashlib
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.datastructures import UploadFile

from app import database as database_module
from app.api import portal
from app.database import Base, get_db
from app.models.claim import Claim
from app.models.claim import AnalysisRun, Document
from app.security.auth import hash_portal_secret, verify_portal_secret
from app.security.rate_limit import PortalSubmissionRateLimitMiddleware
from app.utils.file_handler import save_upload


def _portal_test_app(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'portal.db'}")

    async def initialize():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize())
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def override_db():
        async with sessions() as session:
            yield session

    app = FastAPI()
    app.include_router(portal.router)
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(database_module, "engine", engine)
    return app, sessions, engine


def test_patient_status_requires_matching_claim_secret(tmp_path, monkeypatch):
    app, sessions, engine = _portal_test_app(tmp_path, monkeypatch)
    claim_id = "claim-private"
    secret = "one-time-secret-that-is-long-and-random"

    async def seed():
        async with sessions() as db:
            db.add(Claim(id=claim_id, patient_name="Private Patient", portal_token=hash_portal_secret(secret), status="PENDING"))
            await db.commit()

    asyncio.run(seed())
    with TestClient(app) as client:
        assert client.get(f"/api/portal/status/{claim_id}").status_code == 404
        assert client.get(f"/api/portal/status/{claim_id}", headers={"X-Portal-Secret": "wrong"}).status_code == 404
        response = client.get(f"/api/portal/status/{claim_id}", headers={"X-Portal-Secret": secret})
        assert response.status_code == 200
        assert response.json()["patient_name"] == "Private Patient"
    asyncio.run(engine.dispose())


def test_strict_upload_validation_rejects_mime_mismatch_and_path_escape(tmp_path):
    async def exercise():
        upload_dir = str(tmp_path / "uploads")
        fake_pdf = UploadFile(file=io.BytesIO(b"not a PDF"), filename="../../escape.pdf")
        try:
            await save_upload(
                fake_pdf,
                upload_dir,
                max_size_mb=1,
                allowed_mime_types={"application/pdf"},
                stored_filename="document.upload",
                validate_content=True,
            )
        except ValueError as exc:
            assert "supported" in str(exc)
        else:
            raise AssertionError("Malformed upload was accepted")

        oversized = UploadFile(file=io.BytesIO(b"%PDF-1.4\n" + b"x" * 100), filename="large.pdf")
        try:
            await save_upload(
                oversized,
                upload_dir,
                max_size_mb=0,
                allowed_mime_types={"application/pdf"},
                stored_filename="large.upload",
                validate_content=True,
            )
        except ValueError as exc:
            assert "limit" in str(exc)
        else:
            raise AssertionError("Oversized upload was accepted")
        assert list((tmp_path / "uploads").glob("*")) == []

    asyncio.run(exercise())


def test_patient_submit_has_request_rate_guard():
    app = FastAPI()
    app.add_middleware(PortalSubmissionRateLimitMiddleware, limit=2, window_seconds=60)

    @app.post("/api/portal/submit")
    async def submit():
        return {"status": "accepted"}

    with TestClient(app) as client:
        assert client.post("/api/portal/submit").status_code == 200
        assert client.post("/api/portal/submit").status_code == 200
        limited = client.post("/api/portal/submit")
        assert limited.status_code == 429
        assert limited.headers["Retry-After"]


def test_portal_submission_secret_is_hash_only_and_idempotent(tmp_path, monkeypatch):
    app, sessions, engine = _portal_test_app(tmp_path, monkeypatch)
    monkeypatch.setattr(portal.settings, "UPLOAD_DIR", str(tmp_path / "safe-uploads"))
    monkeypatch.setattr(portal, "_trigger_analysis", lambda *_args: asyncio.sleep(0))
    secret = "A" * 43
    payload = {
        "patient_name": "Private Patient",
        "patient_email": "patient@example.test",
        "patient_phone": "",
        "hospital_bill": ("bill.pdf", b"%PDF-1.4\nbill", "application/pdf"),
        "insurance_policy": ("policy.pdf", b"%PDF-1.4\npolicy", "application/pdf"),
        "rejection_letter": ("decision.pdf", b"%PDF-1.4\ndecision", "application/pdf"),
    }

    with TestClient(app) as client:
        first = client.post("/api/portal/submit", data={key: val for key, val in payload.items() if not isinstance(val, tuple)}, files={key: val for key, val in payload.items() if isinstance(val, tuple)}, headers={"X-Portal-Secret": secret})
        assert first.status_code == 200, first.text
        first_body = first.json()
        second = client.post("/api/portal/submit", data={key: val for key, val in payload.items() if not isinstance(val, tuple)}, files={key: val for key, val in payload.items() if isinstance(val, tuple)}, headers={"X-Portal-Secret": secret})
        assert second.status_code == 200, second.text
        assert second.json()["claim_id"] == first_body["claim_id"]

    async def inspect():
        async with sessions() as db:
            claim = await db.get(Claim, first_body["claim_id"])
            docs = (await db.execute(select(Document).where(Document.claim_id == claim.id))).scalars().all()
            assert claim.portal_token != secret
            assert verify_portal_secret(secret, claim.portal_token)
            assert len(docs) == 3
            assert all(doc.file_path.endswith(".pdf") for doc in docs)

    asyncio.run(inspect())
    asyncio.run(engine.dispose())


def test_portal_submission_cleans_prior_files_when_later_storage_save_fails(tmp_path, monkeypatch):
    app, sessions, engine = _portal_test_app(tmp_path, monkeypatch)
    upload_root = tmp_path / "uploads-on-storage-error"
    monkeypatch.setattr(portal.settings, "UPLOAD_DIR", str(upload_root))
    calls = 0

    async def fail_second_save(upload_file, upload_dir, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated disk write failure")
        path = Path(upload_dir) / kwargs["stored_filename"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"%PDF-1.4\nfirst")
        return str(path), "application/pdf", path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()

    monkeypatch.setattr(portal, "save_upload", fail_second_save)
    payload = {
        "patient_name": "Storage Failure Patient",
        "patient_email": "patient@example.test",
        "patient_phone": "",
        "hospital_bill": ("bill.pdf", b"%PDF-1.4\nbill", "application/pdf"),
        "insurance_policy": ("policy.pdf", b"%PDF-1.4\npolicy", "application/pdf"),
        "rejection_letter": ("decision.pdf", b"%PDF-1.4\ndecision", "application/pdf"),
    }

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/portal/submit",
            data={key: val for key, val in payload.items() if not isinstance(val, tuple)},
            files={key: val for key, val in payload.items() if isinstance(val, tuple)},
        )

    assert response.status_code == 500
    assert list(upload_root.rglob("*.upload")) == []

    async def inspect():
        async with sessions() as db:
            assert (await db.execute(select(Claim))).scalars().all() == []

    asyncio.run(inspect())
    asyncio.run(engine.dispose())


def test_portal_rejects_submission_when_durable_analysis_queue_is_full(tmp_path, monkeypatch):
    app, sessions, engine = _portal_test_app(tmp_path, monkeypatch)
    upload_root = tmp_path / "uploads-queue-full"
    monkeypatch.setattr(
        portal,
        "settings",
        SimpleNamespace(UPLOAD_DIR=str(upload_root), MAX_UPLOAD_SIZE_MB=25, MAX_SUBMISSION_SIZE_MB=50, MAX_PENDING_ANALYSIS_JOBS=1),
    )
    monkeypatch.setattr(portal, "_trigger_analysis", lambda *_args: asyncio.sleep(0))

    async def seed_pending_job():
        async with sessions() as db:
            claim = Claim(id="already-queued", patient_name="Queued Patient", portal_token=hash_portal_secret("a" * 43), status="QUEUED")
            db.add(claim)
            db.add(AnalysisRun(id="pending-run", claim_id=claim.id, status="PENDING"))
            await db.commit()

    asyncio.run(seed_pending_job())
    payload = {
        "patient_name": "Additional Patient",
        "patient_email": "patient@example.test",
        "patient_phone": "",
        "hospital_bill": ("bill.pdf", b"%PDF-1.4\nbill", "application/pdf"),
        "insurance_policy": ("policy.pdf", b"%PDF-1.4\npolicy", "application/pdf"),
        "rejection_letter": ("decision.pdf", b"%PDF-1.4\ndecision", "application/pdf"),
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/portal/submit",
            data={key: val for key, val in payload.items() if not isinstance(val, tuple)},
            files={key: val for key, val in payload.items() if isinstance(val, tuple)},
        )

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "30"
    assert list(upload_root.rglob("*.upload")) == []

    async def inspect():
        async with sessions() as db:
            claims = (await db.execute(select(Claim))).scalars().all()
            assert len(claims) == 1 and claims[0].id == "already-queued"

    asyncio.run(inspect())
    asyncio.run(engine.dispose())


def test_portal_enforces_total_submission_byte_budget_before_saving(tmp_path, monkeypatch):
    app, sessions, engine = _portal_test_app(tmp_path, monkeypatch)
    upload_root = tmp_path / "uploads-total-budget"
    monkeypatch.setattr(
        portal,
        "settings",
        SimpleNamespace(
            UPLOAD_DIR=str(upload_root), MAX_UPLOAD_SIZE_MB=25,
            MAX_SUBMISSION_SIZE_MB=2, MAX_PENDING_ANALYSIS_JOBS=10,
        ),
    )
    payload = {
        "patient_name": "Budget Patient",
        "patient_email": "patient@example.test",
        "patient_phone": "",
        "hospital_bill": ("bill.pdf", b"%PDF-1.4\n" + b"a" * (1024 * 1024), "application/pdf"),
        "insurance_policy": ("policy.pdf", b"%PDF-1.4\n" + b"b" * (1024 * 1024), "application/pdf"),
        "rejection_letter": ("decision.pdf", b"%PDF-1.4\n" + b"c" * (1024 * 1024), "application/pdf"),
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/portal/submit",
            data={key: val for key, val in payload.items() if not isinstance(val, tuple)},
            files={key: val for key, val in payload.items() if isinstance(val, tuple)},
        )

    assert response.status_code == 413
    assert not list(upload_root.rglob("*"))

    async def inspect():
        async with sessions() as db:
            assert (await db.execute(select(Claim))).scalars().all() == []

    asyncio.run(inspect())
    asyncio.run(engine.dispose())


def test_patient_websocket_authenticates_before_sending_claim_status(tmp_path, monkeypatch):
    app, sessions, engine = _portal_test_app(tmp_path, monkeypatch)
    claim_id = "claim-ws-private"
    secret = "one-time-secret-that-is-long-and-random"

    async def seed():
        async with sessions() as db:
            db.add(Claim(id=claim_id, patient_name="Private Patient", portal_token=hash_portal_secret(secret), status="PENDING"))
            await db.commit()

    asyncio.run(seed())
    with TestClient(app) as client:
        ws_headers = {"origin": "http://localhost:5174"}
        with client.websocket_connect(f"/api/portal/ws/claim/{claim_id}", headers=ws_headers) as websocket:
            websocket.send_text(secret)
            assert websocket.receive_json()["status"] == "PENDING"
        try:
            with client.websocket_connect(f"/api/portal/ws/claim/{claim_id}", headers=ws_headers) as websocket:
                websocket.send_text("invalid")
                websocket.receive_json()
            assert False, "Invalid portal secret should close the WebSocket"
        except Exception as exc:
            assert getattr(exc, "code", None) == 4401
        try:
            with client.websocket_connect(f"/api/portal/ws/claim/{claim_id}", headers={"origin": "https://attacker.example"}) as websocket:
                websocket.send_text(secret)
                websocket.receive_json()
            assert False, "Cross-origin WebSocket should be rejected"
        except Exception as exc:
            assert getattr(exc, "code", None) == 4403
    asyncio.run(engine.dispose())
