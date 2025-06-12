---
description: Example configurations for using S3 with KMS encryption in Seldon Core, including handling MD5 checksum mismatch issues with rclone.
---

# S3 KMS Encryption Configuration Examples

This document provides example configurations for using AWS S3 with KMS encryption in Seldon Core, particularly addressing MD5 checksum mismatch issues that occur with server-side encryption.

## Understanding the MD5 Checksum Issue

When using server-side encryption with KMS on S3, the ETag header is no longer the MD5 sum of the data. This causes rclone's checksum validation to fail because the MD5 hash calculated locally doesn't match what S3 returns. This results in "corrupted on transfer: MD5 hash differ" errors.

## Configuration Examples

### Basic S3 with KMS Encryption

```yaml
# S3 with KMS encryption secret
apiVersion: v1
kind: Secret
metadata:
  name: s3-kms-secret
  namespace: seldon-mesh
type: Opaque
stringData:
  s3: |
    type: s3
    name: s3
    parameters:
      provider: AWS
      env_auth: false
      access_key_id: YOUR_ACCESS_KEY_ID
      secret_access_key: YOUR_SECRET_ACCESS_KEY
      region: us-east-1
      server_side_encryption: aws:kms
      sse_kms_key_id: arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
```

### S3 with KMS and Checksum Handling

For cases where you need to skip checksum validation due to KMS encryption:

```yaml
# S3 with KMS encryption and checksum skip
apiVersion: v1
kind: Secret
metadata:
  name: s3-kms-no-checksum
  namespace: seldon-mesh
type: Opaque
stringData:
  s3: |
    type: s3
    name: s3
    parameters:
      provider: AWS
      env_auth: false
      access_key_id: YOUR_ACCESS_KEY_ID
      secret_access_key: YOUR_SECRET_ACCESS_KEY
      region: us-east-1
      server_side_encryption: aws:kms
      sse_kms_key_id: arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
      disable_checksum: true
      no_check_bucket: true
```

### S3 with Default KMS Encryption

For buckets using default KMS encryption:

```yaml
# S3 with default KMS encryption
apiVersion: v1
kind: Secret
metadata:
  name: s3-default-kms
  namespace: seldon-mesh
type: Opaque
stringData:
  s3: |
    type: s3
    name: s3
    parameters:
      provider: AWS
      env_auth: false
      access_key_id: YOUR_ACCESS_KEY_ID
      secret_access_key: YOUR_SECRET_ACCESS_KEY
      region: us-east-1
      server_side_encryption: aws:kms
      # No sse_kms_key_id specified - uses bucket default
```

### S3 with Customer-Managed KMS Key

```yaml
# S3 with customer-managed KMS key
apiVersion: v1
kind: Secret
metadata:
  name: s3-customer-kms
  namespace: seldon-mesh
type: Opaque
stringData:
  s3: |
    type: s3
    name: s3
    parameters:
      provider: AWS
      env_auth: false
      access_key_id: YOUR_ACCESS_KEY_ID
      secret_access_key: YOUR_SECRET_ACCESS_KEY
      region: us-east-1
      server_side_encryption: aws:kms
      sse_kms_key_id: alias/my-custom-key
      sse_customer_key_md5: YOUR_KEY_MD5_IF_USING_SSE_C
```

## Using with Models

### Model with KMS-Encrypted S3 Storage

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: my-kms-model
spec:
  storageUri: "s3://my-encrypted-bucket/models/my-model"
  secretName: "s3-kms-secret"
  requirements:
  - sklearn
  memory: 1Gi
```

### Model with Checksum Skip

```yaml
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: my-model-no-checksum
spec:
  storageUri: "s3://my-encrypted-bucket/models/my-model"
  secretName: "s3-kms-no-checksum"
  requirements:
  - tensorflow
  memory: 2Gi
```

## Troubleshooting

### Common Error Messages

1. **"corrupted on transfer: MD5 hash differ"**
   - This occurs when KMS encryption is not properly configured
   - Solution: Add `server_side_encryption: aws:kms` to your rclone parameters

2. **"AccessDenied: Access Denied"**
   - Ensure your IAM role/user has the necessary KMS permissions
   - Required permissions: `kms:Decrypt`, `kms:GenerateDataKey`

3. **"The specified method is not allowed against this resource"**
   - This can occur when trying to use wrong encryption settings
   - Verify the bucket's encryption configuration matches your settings

### Best Practices

1. **Always specify encryption type**: Explicitly set `server_side_encryption` parameter
2. **Use IAM roles when possible**: Set `env_auth: true` to use IAM roles instead of keys
3. **Test connectivity**: Use `seldon model status` to verify model can access storage
4. **Monitor logs**: Check agent logs for detailed rclone error messages

## Advanced Configuration

### S3 with Multiple Encryption Types

For environments with mixed encryption requirements:

```yaml
# S3 with conditional encryption
apiVersion: v1
kind: Secret
metadata:
  name: s3-mixed-encryption
  namespace: seldon-mesh
type: Opaque
stringData:
  s3-kms: |
    type: s3
    name: s3-kms
    parameters:
      provider: AWS
      env_auth: true
      region: us-east-1
      server_side_encryption: aws:kms
      sse_kms_key_id: arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
  s3-sse: |
    type: s3
    name: s3-sse
    parameters:
      provider: AWS
      env_auth: true
      region: us-east-1
      server_side_encryption: AES256
```

### Rclone Command-Line Flags

When debugging, you can use these rclone flags:
- `--ignore-checksum`: Skip checksum validation entirely
- `--s3-disable-checksum`: Disable checksum for large objects
- `--s3-server-side-encryption aws:kms`: Specify KMS encryption
- `--s3-sse-kms-key-id <key-id>`: Specify the KMS key ID

## References

- [Rclone S3 Documentation](https://rclone.org/s3/)
- [AWS S3 Server-Side Encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html)
- [Seldon Storage Secrets Documentation](./storage-secrets.md)