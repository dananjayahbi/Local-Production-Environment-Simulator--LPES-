"""
SSL certificate management for LPES.
Handles certificate generation, storage, and validation.
"""

import os
import ssl
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from lpes.core.config import LPESConfig


logger = logging.getLogger(__name__)


class SSLManager:
    """Manages SSL certificates for LPES projects."""
    
    def __init__(self, config: Optional[LPESConfig] = None):
        self.config = config or LPESConfig()
        self._ca_cert: Optional[x509.Certificate] = None
        self._ca_key: Optional[rsa.RSAPrivateKey] = None
        self._ensure_ca_exists()
    
    def _ensure_ca_exists(self):
        """Ensure Certificate Authority exists, create if not."""
        ca_cert_path = self.config.get_ca_cert_path()
        ca_key_path = self.config.get_ca_key_path()
        
        if ca_cert_path.exists() and ca_key_path.exists():
            try:
                self._load_ca()
                logger.info("Loaded existing Certificate Authority")
                return
            except Exception as e:
                logger.warning(f"Failed to load existing CA: {e}")
        
        logger.info("Creating new Certificate Authority")
        self._create_ca()
    
    def _create_ca(self):
        """Create a new Certificate Authority."""
        # Generate CA private key
        self._ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Development"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "LPES Certificate Authority"),
            x509.NameAttribute(NameOID.COMMON_NAME, "LPES Local CA"),
        ])
        
        self._ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self._ca_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=3650)  # 10 years
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(self._ca_key.public_key()),
            critical=False,
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(self._ca_key.public_key()),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).sign(self._ca_key, hashes.SHA256(), default_backend())
        
        # Save CA certificate and key
        self._save_ca()
        logger.info("Created new Certificate Authority")
    
    def _load_ca(self):
        """Load existing Certificate Authority."""
        ca_cert_path = self.config.get_ca_cert_path()
        ca_key_path = self.config.get_ca_key_path()
        
        # Load certificate
        with open(ca_cert_path, 'rb') as f:
            self._ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
        
        # Load private key
        with open(ca_key_path, 'rb') as f:
            self._ca_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
    
    def _save_ca(self):
        """Save Certificate Authority to disk."""
        ca_cert_path = self.config.get_ca_cert_path()
        ca_key_path = self.config.get_ca_key_path()
        
        # Save certificate
        with open(ca_cert_path, 'wb') as f:
            f.write(self._ca_cert.public_bytes(serialization.Encoding.PEM))
        
        # Save private key
        with open(ca_key_path, 'wb') as f:
            f.write(self._ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Set restrictive permissions
        os.chmod(ca_key_path, 0o600)
    
    def generate_certificate(self, domain: str, include_subdomains: bool = True) -> Tuple[str, str]:
        """
        Generate SSL certificate for a domain.
        
        Returns:
            Tuple of (certificate_path, private_key_path)
        """
        logger.info(f"Generating SSL certificate for {domain}")
        
        # Check if certificate already exists and is valid
        cert_path = self.config.get_ssl_cert_path(domain)
        key_path = self.config.get_ssl_key_path(domain)
        
        if cert_path.exists() and key_path.exists():
            if self._is_certificate_valid(cert_path, domain):
                logger.info(f"Valid certificate already exists for {domain}")
                return str(cert_path), str(key_path)
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Development"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "LPES Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, domain),
        ])
        
        # Build certificate
        cert_builder = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self._ca_cert.subject
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)  # 1 year
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False,
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(self._ca_key.public_key()),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=True,
        )
        
        # Add Subject Alternative Names
        san_list = [x509.DNSName(domain)]
        if include_subdomains:
            san_list.append(x509.DNSName(f"*.{domain}"))
        
        cert_builder = cert_builder.add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        )
        
        # Sign certificate with CA
        certificate = cert_builder.sign(self._ca_key, hashes.SHA256(), default_backend())
        
        # Save certificate and key
        self._save_certificate(domain, certificate, private_key)
        
        logger.info(f"Generated SSL certificate for {domain}")
        return str(cert_path), str(key_path)
    
    def _save_certificate(self, domain: str, certificate: x509.Certificate, 
                         private_key: rsa.RSAPrivateKey):
        """Save certificate and private key to disk."""
        cert_path = self.config.get_ssl_cert_path(domain)
        key_path = self.config.get_ssl_key_path(domain)
        
        # Save certificate
        with open(cert_path, 'wb') as f:
            f.write(certificate.public_bytes(serialization.Encoding.PEM))
        
        # Save private key
        with open(key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Set restrictive permissions on private key
        os.chmod(key_path, 0o600)
    
    def _is_certificate_valid(self, cert_path: Path, domain: str) -> bool:
        """Check if existing certificate is valid."""
        try:
            with open(cert_path, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            # Check expiration
            if cert.not_valid_after <= datetime.utcnow():
                return False
            
            # Check domain
            try:
                san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                domains = [name.value for name in san_ext.value]
                if domain not in domains and f"*.{domain.split('.', 1)[-1]}" not in domains:
                    return False
            except x509.ExtensionNotFound:
                # Check common name
                try:
                    cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                    if cn != domain:
                        return False
                except (IndexError, AttributeError):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to validate certificate {cert_path}: {e}")
            return False
    
    def get_ssl_context(self, domain: str) -> ssl.SSLContext:
        """Get SSL context for a domain."""
        cert_path, key_path = self.generate_certificate(domain)
        
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_path, key_path)
        
        return context
    
    def list_certificates(self) -> List[Tuple[str, datetime, bool]]:
        """
        List all certificates with their expiration dates and validity.
        
        Returns:
            List of tuples: (domain, expiration_date, is_valid)
        """
        certificates = []
        
        for cert_file in self.config.ssl_dir.glob("*.crt"):
            domain = cert_file.stem
            try:
                with open(cert_file, 'rb') as f:
                    cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                
                expiration = cert.not_valid_after
                is_valid = expiration > datetime.utcnow()
                
                certificates.append((domain, expiration, is_valid))
                
            except Exception as e:
                logger.warning(f"Failed to read certificate {cert_file}: {e}")
        
        return sorted(certificates, key=lambda x: x[1])  # Sort by expiration date
    
    def revoke_certificate(self, domain: str) -> bool:
        """Remove certificate files for a domain."""
        cert_path = self.config.get_ssl_cert_path(domain)
        key_path = self.config.get_ssl_key_path(domain)
        
        removed = False
        
        if cert_path.exists():
            cert_path.unlink()
            removed = True
        
        if key_path.exists():
            key_path.unlink()
            removed = True
        
        if removed:
            logger.info(f"Revoked certificate for {domain}")
        else:
            logger.warning(f"No certificate found for {domain}")
        
        return removed
    
    def get_ca_certificate_pem(self) -> str:
        """Get CA certificate in PEM format for trust installation."""
        if self._ca_cert is None:
            raise ValueError("CA certificate not available")
        
        return self._ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
    
    def get_trust_instructions(self) -> str:
        """Get instructions for trusting the CA certificate."""
        ca_cert_path = self.config.get_ca_cert_path()
        
        instructions = f"""
To trust LPES certificates in your browser, you need to add the Certificate Authority to your system's trust store:

CA Certificate Location: {ca_cert_path}

Instructions by Operating System:

=== Windows ===
1. Open the Start menu and search for "Manage computer certificates"
2. Navigate to "Trusted Root Certification Authorities" → "Certificates"
3. Right-click and select "All Tasks" → "Import..."
4. Import the CA certificate file: {ca_cert_path}

=== macOS ===
1. Open Keychain Access
2. Drag the CA certificate file to the "System" keychain
3. Double-click the certificate and set "Trust" to "Always Trust"

=== Linux (Ubuntu/Debian) ===
1. Copy the certificate: sudo cp {ca_cert_path} /usr/local/share/ca-certificates/lpes-ca.crt
2. Update certificates: sudo update-ca-certificates

=== Browser-specific (Alternative) ===
Firefox:
1. Go to Settings → Privacy & Security → Certificates → View Certificates
2. Import the CA certificate file

Chrome:
1. Go to Settings → Advanced → Privacy and security → Manage certificates
2. Import the CA certificate to "Trusted Root Certification Authorities"

After installing the CA certificate, restart your browser for changes to take effect.
"""
        return instructions
