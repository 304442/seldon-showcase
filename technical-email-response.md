# Technical Support Response: AWS MSK Integration and S3 KMS Model Download Issues with Seldon Core 2

Dear [Customer Name],

Thank you for reaching out regarding the AWS MSK Kafka setup and S3 KMS encryption issues you're experiencing with Seldon Core 2. I've thoroughly analyzed your situation and prepared a comprehensive solution guide based on official AWS and Seldon documentation.

## Executive Summary

The issues you're experiencing stem from two distinct configuration challenges:
1. **AWS MSK Authentication**: Requires proper SASL/SCRAM or mTLS configuration with correct ACL permissions
2. **S3 KMS Encryption**: MD5 checksum mismatches occur because KMS-encrypted objects don't provide standard ETags

## Issue 1: AWS MSK Kafka Setup

### Root Cause Analysis

Based on AWS MSK documentation and Seldon Core integration requirements, common failure points include:
- Incorrect bootstrap broker endpoints (public vs. VPC-internal)
- Missing or misconfigured ACL permissions
- Replication factor mismatches with MSK cluster settings
- Authentication credential issues

### Solution Implementation

#### For SASL/SCRAM Authentication:

1. **Create Kubernetes Secret for Credentials**:
```bash
kubectl create secret generic aws-msk-kafka-secret \
  -n seldon-mesh \
  --from-literal password="<YOUR_MSK_SASL_PASSWORD>"
```

2. **Configure Seldon Core 2 Helm Values**:
```yaml
kafka:
  bootstrap: <your-msk-bootstrap-endpoints>:9094  # Note: Use port 9094 for SASL_SSL
  topics:
    replicationFactor: 3  # Must match MSK min.insync.replicas
    numPartitions: 4
  debug: all  # Enable for troubleshooting

security:
  kafka:
    protocol: SASL_SSL
    sasl:
      mechanism: SCRAM-SHA-512
      client:
        username: <your-username>
        secret: aws-msk-kafka-secret
        passwordPath: password
    ssl:
      client:
        secret:
        brokerValidationSecret:
```

#### For mTLS Authentication:

1. **Create TLS Secrets**:
```bash
# Client certificate secret
kubectl create secret generic aws-msk-client \
  --from-file=./tls.key \
  --from-file=./tls.crt \
  --from-file=./ca.crt \
  -n seldon-mesh

# Broker CA secret
kubectl create secret generic aws-msk-broker-ca \
  --from-file=./ca.crt \
  -n seldon-mesh
```

2. **Configure ACLs on MSK** (critical step often missed):
```bash
# Full topic access
kafka-acls.sh --bootstrap-server <mTLS-endpoint> \
  --add --allow-principal User:CN=<your-cert-CN> \
  --operation All --topic '*' \
  --command-config client.properties

# Cluster admin access (required for topic creation)
kafka-acls.sh --bootstrap-server <mTLS-endpoint> \
  --add --allow-principal User:CN=<your-cert-CN> \
  --operation All --cluster '*' \
  --command-config client.properties

# Consumer group access
kafka-acls.sh --bootstrap-server <mTLS-endpoint> \
  --add --allow-principal User:CN=<your-cert-CN> \
  --operation All --group '*' \
  --command-config client.properties
```

### Troubleshooting Steps

1. **Verify Connectivity**:
```bash
telnet <bootstrap-broker> 9094
```

2. **Check MSK Cluster Health**:
- Monitor `ActiveControllerCount` metric (must be 1)
- Verify `UnderReplicatedPartitions` metric (should be 0)
- Check `KafkaDataLogsDiskUsed` to ensure storage isn't full

3. **Common Error Resolutions**:
- **"Not enough insync replicas"**: Set `kafka.topics.replicationFactor` to match MSK's `min.insync.replicas` (typically 2 or 3)
- **"Too many connects"**: For `kafka.t3.small` instances, increase `reconnect.backoff.ms` to 1000 or upgrade to larger instance type
- **Authentication failures**: Ensure correct bootstrap endpoints (use public endpoints if accessing from outside VPC)

## Issue 2: S3 KMS Encryption & MD5 Mismatch

### Root Cause Analysis

When S3 objects are encrypted with KMS:
- The ETag header is no longer the MD5 hash of the object data
- Rclone's default checksum validation fails
- This is documented behavior per AWS S3 documentation

### Solution Implementation

1. **Create Proper Rclone Configuration Secret**:
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
      env_auth: false  # Or true if using IAM roles
      access_key_id: <YOUR_ACCESS_KEY>
      secret_access_key: <YOUR_SECRET_KEY>
      region: <YOUR_REGION>
      endpoint: https://s3.<YOUR_REGION>.amazonaws.com
      server_side_encryption: aws:kms
      sse_kms_key_id: arn:aws:kms:<region>:<account>:key/<key-id>
      # Critical: Disable checksum for KMS-encrypted objects
      disable_checksum: true
      # Alternative approach if above doesn't work
      no_check_bucket: true
```

2. **Configure Model to Use the Secret**:
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
  memory: 1Gi
```

3. **Alternative: Configure as Preloaded Secret** (for multiple models):

Update your SeldonRuntime or Helm values:
```yaml
config:
  agentConfig:
    rclone:
      configSecrets:
        - seldon-rclone-gs-public
        - s3-kms-models  # Add your KMS secret here
```

### Additional Considerations

1. **IAM Permissions Required**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket",
        "arn:aws:s3:::your-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:region:account:key/key-id"
    }
  ]
}
```

2. **Testing Rclone Configuration**:
```bash
# Test directly with rclone (in a debug pod)
rclone ls s3-kms:your-bucket/path --config=/path/to/rclone.conf --s3-disable-checksum
```

## Recommended Action Plan

1. **Immediate Actions**:
   - Enable debug logging (`kafka.debug=all`) to capture detailed error messages
   - Verify all bootstrap endpoints and ports are correct
   - Confirm IAM/KMS permissions are properly configured

2. **Implementation Sequence**:
   - First, resolve MSK connectivity issues
   - Then, configure S3 KMS secrets with checksum disabled
   - Test with a simple model before deploying production workloads

3. **Monitoring**:
   - Set up CloudWatch alarms for MSK metrics
   - Monitor Seldon pod logs for storage initialization errors
   - Track model download times to ensure KMS isn't causing timeouts

## Next Steps

Please implement these configurations and let me know if you encounter any specific error messages. I'm available to help debug any issues that arise during implementation.

For reference, I've based this guidance on:
- [Seldon Core 2 AWS MSK Documentation](https://docs.seldon.io/projects/seldon-core/en/latest/contents/getting-started/kubernetes-installation/security/aws-msk-sasl.html)
- [AWS MSK Troubleshooting Guide](https://docs.aws.amazon.com/msk/latest/developerguide/troubleshooting.html)
- [Rclone S3 Documentation](https://rclone.org/s3/)
- Real-world deployment experiences documented in the rclone forums

Best regards,
[Your Name]
Senior Solutions Engineer