#!/bin/bash
# Zero-Trust Certificate Management Script
# Generates and manages mTLS certificates for service-to-service communication

set -e

# Configuration
NAMESPACE=${NAMESPACE:-default}
CERT_DIR="./certs"
CA_KEY="${CERT_DIR}/ca.key"
CA_CERT="${CERT_DIR}/ca.crt"
VALIDITY_DAYS=365

# Services requiring mTLS
SERVICES=(
    "beryl-core-api"
    "graphql-gateway"
    "event-bus"
    "fintech-adapter"
    "mobility-adapter"
    "esg-adapter"
    "social-adapter"
)

# Create certificate directory
mkdir -p "${CERT_DIR}"

echo "🔐 Generating Zero-Trust mTLS Certificates..."

# Generate CA private key and certificate
if [ ! -f "${CA_KEY}" ]; then
    echo "Generating CA private key..."
    openssl genrsa -out "${CA_KEY}" 4096

    echo "Generating CA certificate..."
    openssl req -x509 -new -nodes -key "${CA_KEY}" -sha256 -days ${VALIDITY_DAYS} \
        -out "${CA_CERT}" \
        -subj "/C=FR/ST=IDF/L=Paris/O=Beryl Ecosystem/CN=Beryl Zero-Trust CA"
fi

# Generate certificates for each service
for service in "${SERVICES[@]}"; do
    echo "Generating certificate for ${service}..."

    key_file="${CERT_DIR}/${service}.key"
    cert_file="${CERT_DIR}/${service}.crt"
    csr_file="${CERT_DIR}/${service}.csr"

    # Generate private key
    openssl genrsa -out "${key_file}" 2048

    # Generate certificate signing request
    openssl req -new -key "${key_file}" -out "${csr_file}" \
        -subj "/C=FR/ST=IDF/L=Paris/O=Beryl Ecosystem/CN=${service}"

    # Generate certificate signed by CA
    openssl x509 -req -in "${csr_file}" -CA "${CA_CERT}" -CAkey "${CA_KEY}" \
        -CAcreateserial -out "${cert_file}" -days ${VALIDITY_DAYS} -sha256 \
        -extfile <(printf "subjectAltName=DNS:${service},DNS:${service}.${NAMESPACE},DNS:${service}.${NAMESPACE}.svc.cluster.local")

    # Create Kubernetes secret
    kubectl create secret tls "${service}-mtls" \
        --cert="${cert_file}" \
        --key="${key_file}" \
        --namespace="${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -

    echo "✅ Certificate generated and secret created for ${service}"
done

# Generate client certificates for external adapters
echo "Generating client certificates for external communication..."

client_key="${CERT_DIR}/client.key"
client_cert="${CERT_DIR}/client.crt"
client_csr="${CERT_DIR}/client.csr"

openssl genrsa -out "${client_key}" 2048
openssl req -new -key "${client_key}" -out "${client_csr}" \
    -subj "/C=FR/ST=IDF/L=Paris/O=Beryl Ecosystem/CN=Beryl Client"
openssl x509 -req -in "${client_csr}" -CA "${CA_CERT}" -CAkey "${CA_KEY}" \
    -CAcreateserial -out "${client_cert}" -days ${VALIDITY_DAYS} -sha256

# Create client certificate secret
kubectl create secret generic beryl-client-certs \
    --from-file=ca.crt="${CA_CERT}" \
    --from-file=tls.crt="${client_cert}" \
    --from-file=tls.key="${client_key}" \
    --namespace="${NAMESPACE}" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "🎉 mTLS certificates generated successfully!"
echo ""
echo "📋 Certificate Summary:"
echo "- CA Certificate: ${CA_CERT}"
echo "- Services with mTLS: ${SERVICES[*]}"
echo "- Client certificates available for external adapters"
echo ""
echo "🔄 Certificate Rotation:"
echo "Run this script again to rotate certificates before expiration"
echo "Current validity: ${VALIDITY_DAYS} days"

# Cleanup CSR files
rm -f "${CERT_DIR}"/*.csr "${CERT_DIR}"/*.srl

echo ""
echo "🔒 Zero-Trust mTLS setup complete!"