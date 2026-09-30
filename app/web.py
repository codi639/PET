"""Local HTTPS web interface for PET."""

from __future__ import annotations

import io
import secrets
import ssl
import tempfile
from datetime import datetime, timedelta, timezone
from functools import wraps
from http import HTTPStatus
from pathlib import Path
from typing import Any, Callable, TypeVar

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.serving import make_server

from core.decryption_manager import DecryptionManager
from core.encryption_manager import EncryptionManager
from core.petkey_manager import PetKeyManager
from core.user_manager import UserManager

# from models.user import User

T = TypeVar("T", bound=Callable[..., Any])


def create_web_app(user_manager: UserManager) -> Flask:
    """Create the server-rendered PET web application."""

    app = Flask(__name__, template_folder="templates", static_folder="static")
    # app.config.update(
    #     SECRET_KEY=secrets.token_bytes(32),
    #     SESSION_COOKIE_HTTPONLY=True,
    #     SESSION_COOKIE_SECURE=True,
    #     SESSION_COOKIE_SAMESITE="Strict",
    #     MAX_CONTENT_LENGTH=256 * 1024 * 1024,
    # )
    app.config["SECRET_KEY"] = secrets.token_bytes(32)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024

    @app.before_request
    def prepare_request() -> None:
        """Load the current user and create a per-session CSRF token."""

        g.user = None
        user_uuid = session.get("user_uuid")
        if user_uuid:
            g.user = user_manager.get_user_by_uuid(user_uuid)
            if g.user is None:
                session.clear()
        session.setdefault("csrf_token", secrets.token_urlsafe(32))

    @app.context_processor
    def provide_template_values() -> dict[str, Any]:
        """Expose the current user and CSRF token to every template."""

        return {"current_user": g.user, "csrf_token": session["csrf_token"]}

    def login_required(view: T) -> T:
        """Require an authenticated PET user for a route."""

        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if g.user is None:
                flash("Sign in to continue.", "error")
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapped  # type: ignore[return-value]

    def valid_csrf_token() -> bool:
        """Validate the token submitted by a state-changing form."""

        submitted_token = request.form.get("csrf_token", "")
        return secrets.compare_digest(submitted_token, session["csrf_token"])

    def uploaded_temp_file(field_name: str, suffix: str = "") -> tuple[Any, Path]:
        """Write one upload to a temporary file without trusting its filename."""

        uploaded_file = request.files.get(field_name)
        if uploaded_file is None or not uploaded_file.filename:
            raise ValueError("Please choose a file.")
        temporary_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            uploaded_file.save(temporary_file)
        finally:
            temporary_file.close()
        return uploaded_file, Path(temporary_file.name)

    @app.get("/")
    def index() -> Any:
        """Show the dashboard or sign-in page."""

        return redirect(url_for("dashboard" if g.user else "login"))

    @app.route("/login", methods=["GET", "POST"])
    def login() -> Any:
        """Authenticate a PET user."""

        if request.method == "POST":
            if not valid_csrf_token():
                return _bad_request("Invalid security token.")
            try:
                user = user_manager.login(
                    request.form.get("username", ""),
                    request.form.get("password", ""),
                )
            except ValueError:
                flash("Invalid username or password.", "error")
            else:
                session.clear()
                session["user_uuid"] = user.uuid
                session["csrf_token"] = secrets.token_urlsafe(32)
                return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register() -> Any:
        """Create a new PET account."""

        if request.method == "POST":
            if not valid_csrf_token():
                return _bad_request("Invalid security token.")
            password = request.form.get("password", "")
            if password != request.form.get("confirm_password", ""):
                flash("Passwords do not match.", "error")
            else:
                try:
                    result = user_manager.create_account(
                        request.form.get("username", ""), password
                    )
                except (RuntimeError, ValueError) as error:
                    flash(str(error), "error")
                else:
                    session.clear()
                    session["user_uuid"] = result.user.uuid
                    session["csrf_token"] = secrets.token_urlsafe(32)
                    flash(
                        "Identity created and stored in the system keyring.", "success"
                    )
                    return redirect(url_for("dashboard"))
        return render_template("register.html")

    @app.post("/logout")
    @login_required
    def logout() -> Any:
        """End the current browser session."""

        if not valid_csrf_token():
            return _bad_request("Invalid security token.")
        session.clear()
        return redirect(url_for("login"))

    @app.get("/dashboard")
    @login_required
    def dashboard() -> Any:
        """Show the authenticated PET workspace."""

        return render_template("dashboard.html", users=user_manager.retrieve_users())

    @app.post("/identity/import")
    @login_required
    def import_identity() -> Any:
        """Import an encrypted identity through the existing PET manager."""

        if not valid_csrf_token():
            return _bad_request("Invalid security token.")
        temporary_path: Path | None = None
        try:
            _, temporary_path = uploaded_temp_file("petkey_file", ".petkey")
            passphrase = request.form.get("passphrase", "")
            password = request.form.get("password", "")
            if password != request.form.get("confirm_password", ""):
                raise ValueError("Passwords do not match.")
            imported_user = PetKeyManager(user_manager).import_identity(
                temporary_path,
                passphrase,
                password,
            )
        except (OSError, PermissionError, ValueError, RuntimeError) as error:
            flash(str(error), "error")
        else:
            session["user_uuid"] = imported_user.uuid
            flash(f"Identity imported for {imported_user.username}.", "success")
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return redirect(url_for("dashboard"))

    @app.post("/identity/export")
    @login_required
    def export_identity() -> Any:
        """Export the current identity as an encrypted download."""

        if not valid_csrf_token():
            return _bad_request("Invalid security token.")
        passphrase = request.form.get("passphrase", "")
        if passphrase != request.form.get("confirm_passphrase", ""):
            flash("Passphrases do not match.", "error")
            return redirect(url_for("dashboard"))
        with tempfile.TemporaryDirectory(prefix="pet-export-") as directory:
            output_path = Path(directory) / f"{g.user.username}.petkey"
            try:
                PetKeyManager(user_manager).export_identity(
                    g.user.uuid, output_path, passphrase
                )
                payload = output_path.read_bytes()
            except (OSError, ValueError) as error:
                flash(str(error), "error")
                return redirect(url_for("dashboard"))
        return send_file(
            io.BytesIO(payload),
            as_attachment=True,
            download_name=f"{g.user.username}.petkey",
            mimetype="application/octet-stream",
        )

    @app.post("/files/encrypt")
    @login_required
    def encrypt_file() -> Any:
        """Encrypt an uploaded file for the selected PET users."""

        if not valid_csrf_token():
            return _bad_request("Invalid security token.")
        temporary_path: Path | None = None
        try:
            uploaded_file, temporary_path = uploaded_temp_file("input_file")
            names = {
                name.strip()
                for name in request.form.get("recipients", "").split(",")
                if name.strip()
            }
            users_by_name = {
                user.username: user for user in user_manager.retrieve_users()
            }
            unknown_names = names - users_by_name.keys()
            if unknown_names:
                raise ValueError(
                    "Unknown recipient: " + ", ".join(sorted(unknown_names))
                )
            recipient_uuids = [users_by_name[name].uuid for name in names]
            result = EncryptionManager(
                user_manager.database_manager, user_manager
            ).encrypt_file(temporary_path, recipient_uuids, g.user.uuid)
            payload = result.output_path.read_bytes()
            result.output_path.unlink(missing_ok=True)
        except (OSError, ValueError) as error:
            flash(str(error), "error")
            return redirect(url_for("dashboard"))
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        download_name = f"{uploaded_file.filename}.pet"
        return send_file(
            io.BytesIO(payload),
            as_attachment=True,
            download_name=download_name,
            mimetype="application/octet-stream",
        )

    @app.post("/files/decrypt")
    @login_required
    def decrypt_file() -> Any:
        """Decrypt an uploaded PET file for the current user."""

        if not valid_csrf_token():
            return _bad_request("Invalid security token.")
        temporary_path: Path | None = None
        try:
            uploaded_file, temporary_path = uploaded_temp_file("pet_file", ".pet")
            result = DecryptionManager(user_manager).decrypt_file(
                temporary_path, g.user.uuid
            )
            payload = result.output_path.read_bytes()
            result.output_path.unlink(missing_ok=True)
        except (OSError, PermissionError, ValueError) as error:
            flash(str(error), "error")
            return redirect(url_for("dashboard"))
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        download_name = Path(uploaded_file.filename or "decrypted-file").stem
        return send_file(
            io.BytesIO(payload),
            as_attachment=True,
            download_name=download_name,
            mimetype="application/octet-stream",
        )

    return app


def _bad_request(message: str) -> tuple[str, int]:
    """Return a plain client-error response for invalid form security tokens."""

    return message, HTTPStatus.BAD_REQUEST


def _create_ephemeral_certificate(directory: Path) -> tuple[Path, Path]:
    """Create a self-signed localhost certificate for one server run."""

    private_key = ec.generate_private_key(ec.SECP256R1())
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "PET local server")]
    )
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(hours=24))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName("localhost"), x509.IPAddress(_localhost_address())]
            ),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    certificate_path = directory / "server-cert.pem"
    key_path = directory / "server-key.pem"
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return certificate_path, key_path


def _localhost_address() -> Any:
    """Return the IP address object required by the certificate SAN."""

    import ipaddress

    return ipaddress.ip_address("127.0.0.1")


def _random_port() -> int:
    """Return a random port from the user/private high-port range."""

    return secrets.randbelow(16384) + 49152


def _build_tls_context(certificate_directory: Path) -> ssl.SSLContext:
    """Create a TLS 1.3-only server context with an ephemeral certificate."""

    certificate_path, key_path = _create_ephemeral_certificate(certificate_directory)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(certificate_path, key_path)
    return context


def run_web_server(user_manager: UserManager) -> None:
    """Run the local HTTPS server until interrupted."""

    app = create_web_app(user_manager)
    with tempfile.TemporaryDirectory(prefix="pet-tls-") as directory:
        tls_context = _build_tls_context(Path(directory))
        server = make_server(
            "127.0.0.1",
            _random_port(),
            app,
            threaded=True,
            ssl_context=tls_context,
        )
        print("Starting web server... [OK]")
        print(f"You can now connect to https://127.0.0.1:{server.server_port}")
        try:
            server.serve_forever()
        finally:
            server.server_close()
