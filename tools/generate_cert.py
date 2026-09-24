from datetime import datetime, timedelta, timezone
from ipaddress import IPv4Address
from pathlib import Path
import argparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_certificate(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "s0P0wn3d-lab")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    (output_dir / "lab-key.pem").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    (output_dir / "lab-cert.pem").write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    print(f"Certificat créé dans {output_dir.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Génère un certificat TLS auto-signé pour le laboratoire")
    parser.add_argument("--output-dir", default="certs")
    args = parser.parse_args()
    generate_certificate(Path(args.output_dir))
