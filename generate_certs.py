import os
from OpenSSL import crypto
from datetime import datetime, timedelta

def generate_self_signed_cert(cert_dir="certs"):
    # Create directory if it doesn't exist
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    
    # Create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # Create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "FI"
    cert.get_subject().ST = "Northern Ostrobothnia"
    cert.get_subject().L = "Oulu"
    cert.get_subject().O = "University of Oulu"
    cert.get_subject().OU = "Distributed Systems"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)  # 10 years
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    
    # Add Subject Alternative Names
    alt_names = [
        b"DNS:localhost", 
        b"DNS:server", 
        b"DNS:fastapi_app", 
        b"DNS:calculator_server",
        b"DNS:calculator_client",
        b"DNS:calculator_consumer",
        b"DNS:fastapi",
        b"DNS:mongodb",
        b"DNS:*.default.svc.cluster.local" # For Kubernetes compatibility
    ]
    
    extensions = [
        crypto.X509Extension(b"subjectAltName", False, b", ".join(alt_names)),
        crypto.X509Extension(b"basicConstraints", True, b"CA:FALSE"),
        crypto.X509Extension(b"keyUsage", True, b"nonRepudiation, digitalSignature, keyEncipherment"),
        crypto.X509Extension(b"extendedKeyUsage", False, b"serverAuth, clientAuth")
    ]
    
    for ext in extensions:
        cert.add_extensions([ext])
    
    cert.sign(k, 'sha256')
    
    # Write cert and key to files
    with open(os.path.join(cert_dir, "cert.pem"), "wb") as cert_file:
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open(os.path.join(cert_dir, "key.pem"), "wb") as key_file:
        key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    print(f"Certificate and key generated in {cert_dir} directory")

if __name__ == "__main__":
    generate_self_signed_cert()