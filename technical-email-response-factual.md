# Technical Support Response: AWS MSK and S3 Model Storage Configuration Issues

Dear [Customer Name],

Thank you for contacting us regarding your AWS MSK Kafka setup and S3 KMS encryption issues with Seldon Core 2. Based on our official documentation, I'm providing the exact configuration steps to resolve both issues.

## Issue 1: AWS MSK Kafka Setup

### Configuration Options

Seldon Core 2 supports two authentication methods for AWS MSK:

#### Option A: SASL/SCRAM Authentication (Available in Seldon Core 2.5.0+)

1. **Create Kubernetes Secret** (docs-gb/aws-msk-sasl.md:25-27):
```bash
kubectl create secret generic aws-msk-kafka-secret -n seldon-mesh --from-literal password="<MSK SASL Password>"
```

2. **Helm Configuration** (docs-gb/aws-msk-sasl.md:33-54):
```yaml
kafka:
  bootstrap: <msk-bootstrap-server-endpoints>
  topics:
    replicationFactor: 3
    numPartitions: 4

security:
    kafka:
      protocol: SASL_SSL
      sasl:
        mechanism: SCRAM-SHA-512
        client:
          username: <username>
          secret: aws-msk-kafka-secret
          passwordPath: password
      ssl:
        client:
          secret:
          brokerValidationSecret:
```

#### Option B: mTLS Authentication

1. **Configure ACLs** (docs-gb/aws-msk-mtls.md:24-39):
```bash
# Topic access
kafka-acls.sh --bootstrap-server <mTLS endpoint> --add --allow-principal User:CN=myname --operation All --topic '*' --command-config client.properties

# Cluster admin access
kafka-acls.sh --bootstrap-server <mTLS endpoint> --add --allow-principal User:CN=myname --operation All --cluster '*' --command-config client.properties

# Group access
kafka-acls.sh --bootstrap-server <mTLS endpoint> --add --allow-principal User:CN=myname --operation All --group '*' --command-config client.properties
```

2. **Create TLS Secrets** (docs-gb/aws-msk-mtls.md:51-71):
```bash
# Client certificate
kubectl create secret generic aws-msk-client --from-file=./tls.key --from-file=./tls.crt --from-file=./ca.crt -n seldon-mesh

# Broker CA certificate
kubectl create secret generic aws-msk-broker-ca --from-file=./ca.crt -n seldon-mesh
```

3. **Helm Configuration** (docs-gb/aws-msk-mtls.md:77-89):
```yaml
kafka:
  bootstrap: <MSK Broker Endpoints>

security:
  kafka:
    protocol: SSL
    ssl:
      client:
        secret: aws-msk-client
        brokerValidationSecret: aws-msk-broker-ca
```

### Critical Troubleshooting Points

1. **Replication Factor Issue** (docs-gb/aws-msk-mtls.md:105-108):
   - Error: "not enough insync replicas"
   - Solution: Set `kafka.topics.replicationFactor` to match AWS MSK's `min.insync.replicas` (default is 2)

2. **Debug Logging** (docs-gb/aws-msk-mtls.md:103):
   - Enable: `kafka.debug=all` in Helm values

3. **Public Access Requirements** (docs-gb/aws-msk-mtls.md:16-17):
   - If Kubernetes cluster is outside AWS, MSK must have public endpoint enabled

## Issue 2: S3 KMS Encryption and MD5 Mismatch

### Understanding the Architecture

Seldon Core 2 uses Rclone to copy model artifacts from storage locations to model servers (docs-gb/rclone.md:7-9). The storage configuration is managed through Kubernetes Secrets.

### S3 Configuration Format

Based on docs-gb/storage-secrets.md, here's the correct format for S3 storage:

1. **Create Storage Secret** (following the pattern from docs-gb/storage-secrets.md:137-155):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: s3-kms-models
  namespace: seldon-mesh
type: Opaque
stringData:
  s3-kms: |
    type: s3
    name: s3-kms
    parameters:
      provider: AWS
      env_auth: false
      access_key_id: <YOUR_ACCESS_KEY>
      secret_access_key: <YOUR_SECRET_KEY>
      region: <YOUR_REGION>
      endpoint: https://s3.<YOUR_REGION>.amazonaws.com
```

**Note**: The documentation shows S3 configuration examples with MinIO (docs-gb/storage-secrets.md:146-154) but doesn't specifically address KMS encryption parameters. For KMS-specific parameters, you'll need to refer to Rclone's S3 documentation as mentioned in docs-gb/storage-secrets.md:47-50.

2. **Reference in Model** (docs-gb/storage-secrets.md:159-170):
```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: your-model
spec:
  storageUri: "s3-kms://your-bucket/path/to/model"
  secretName: "s3-kms-models"
  requirements:
  - sklearn
```

3. **Alternative: Preloaded Secrets** (docs-gb/storage-secrets.md:99-109):
```yaml
config:
  agentConfig:
    rclone:
      configSecrets:
        - seldon-rclone-gs-public
        - s3-kms-models
```

### Important Configuration Notes

- Remote name in the secret must match the prefix in `storageUri` (docs-gb/storage-secrets.md:41-42)
- Use Rclone config format, not env var format (docs-gb/storage-secrets.md:49-50)
- Each secret should contain exactly one Rclone configuration (docs-gb/storage-secrets.md:58)

## Recommended Next Steps

1. **For AWS MSK**:
   - Verify your MSK cluster configuration matches Seldon requirements
   - Enable debug logging to capture detailed error messages
   - Ensure replication factor alignment

2. **For S3 KMS**:
   - Create the storage secret with proper S3 configuration
   - For KMS-specific parameters (like checksum handling), consult Rclone S3 documentation as referenced in docs-gb/storage-secrets.md:44-53
   - Test model loading with a simple model first

## References

All configurations provided above are directly from:
- docs-gb/aws-msk-mtls.md
- docs-gb/aws-msk-sasl.md
- docs-gb/storage-secrets.md
- docs-gb/rclone.md

For AWS MSK troubleshooting, please also refer to AWS MSK documentation as mentioned in docs-gb/aws-msk-mtls.md:99 and docs-gb/aws-msk-sasl.md:60.

Best regards,
[Your Name]
Technical Support Team