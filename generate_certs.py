import os  # For creating directories and working with file paths
from OpenSSL import crypto  # Python wrapper for OpenSSL library
from datetime import datetime, timedelta  # For certificate validity periods

def generate_self_signed_cert(cert_dir="certs"):
    """
    Generate a self-signed TLS certificate for secure communications.
    
    This function creates both a private key and a self-signed X.509 certificate
    with multiple subject alternative names for various service hostnames.
    
    Args:
        cert_dir: Directory where certificate files will be saved (defaults to "certs")
    """
    # Create directory if it doesn't exist
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    
    # Create a key pair (RSA, 2048 bits - industry standard for good security)
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)  # RSA key with 2048-bit strength
    
    # Create a self-signed cert
    cert = crypto.X509()
    # Set certificate subject details (who the certificate belongs to)
    cert.get_subject().C = "FI"  # Country code (Finland)
    cert.get_subject().ST = "Northern Ostrobothnia"  # State/Province
    cert.get_subject().L = "Oulu"  # Locality/City
    cert.get_subject().O = "University of Oulu"  # Organization name
    cert.get_subject().OU = "Distributed Systems"  # Organizational Unit
    cert.get_subject().CN = "localhost"  # Common Name (primary domain)
    cert.set_serial_number(1000)  # Unique serial number for this certificate
    cert.gmtime_adj_notBefore(0)  # Valid starting immediately (0 seconds from now)
    cert.gmtime_adj_notAfter(10*365*24*60*60)  # Valid for 10 years (in seconds)
    cert.set_issuer(cert.get_subject())  # Self-signed: issuer = subject
    cert.set_pubkey(k)  # Add the public key to the certificate
    
    # Add Subject Alternative Names (SANs)
    # This allows the certificate to be valid for multiple domain names/hostnames
    alt_names = [
        b"DNS:localhost",  # For local development
        b"DNS:server",  # gRPC server service name
        b"DNS:fastapi_app",  # FastAPI service name
        b"DNS:calculator_server",  # Calculator server container name
        b"DNS:calculator_client",  # Calculator client container name
        b"DNS:calculator_consumer",  # Calculator consumer container name
        b"DNS:fastapi",  # Short name for FastAPI service
        b"DNS:mongodb",  # MongoDB service name
        b"DNS:*.default.svc.cluster.local"  # Kubernetes internal domain pattern
    ]
    
    # Define certificate extensions (additional properties and constraints)
    extensions = [
        crypto.X509Extension(b"subjectAltName", False, b", ".join(alt_names)),  # Add all SANs
        crypto.X509Extension(b"basicConstraints", True, b"CA:FALSE"),  # Not a Certificate Authority
        crypto.X509Extension(b"keyUsage", True, b"nonRepudiation, digitalSignature, keyEncipherment"),  # Allowed key uses
        crypto.X509Extension(b"extendedKeyUsage", False, b"serverAuth, clientAuth")  # Can be used for both server and client authentication
    ]
    
    # Add all extensions to the certificate
    for ext in extensions:
        cert.add_extensions([ext])
    
    # Sign the certificate with our own private key (self-signing)
    cert.sign(k, 'sha256')  # SHA-256 is the secure hashing algorithm used
    
    # Write cert and key to files in PEM format (Base64 encoded DER)
    with open(os.path.join(cert_dir, "cert.pem"), "wb") as cert_file:
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open(os.path.join(cert_dir, "key.pem"), "wb") as key_file:
        key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    print(f"Certificate and key generated in {cert_dir} directory")

# Execute certificate generation when script is run directly
if __name__ == "__main__":
    generate_self_signed_cert()