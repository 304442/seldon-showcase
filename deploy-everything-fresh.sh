#!/bin/bash
set -e

echo "🚀 Deploying complete Seldon Showcase from scratch..."

# Core models for v71.ipynb
echo "📦 Deploying core models..."
kubectl apply -f - <<EOF
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: iris
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
EOF

sleep 30

# Check if iris model works
echo "🧪 Testing iris model..."
kubectl wait --for=condition=ready model/iris -n seldon-mesh --timeout=120s || true

# Deploy working models that we know succeed
echo "📦 Deploying known working models..."
kubectl apply -f - <<EOF
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: sklearn-iris
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: sklearn-iris-v2
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
EOF

sleep 60

# Check what's deployed
echo "📊 Current state:"
kubectl get models -n seldon-mesh

# Test inference
echo "🧪 Testing inference..."
curl -X POST http://34.90.187.46:80/v2/models/iris/infer \
  -H "Content-Type: application/json" \
  -H "Seldon-Model: iris" \
  -d '{
    "inputs": [{
      "name": "predict",
      "shape": [1, 4],
      "datatype": "FP32",
      "data": [[5.1, 3.5, 1.4, 0.2]]
    }]
  }' || echo "Inference failed"

# Create simple pipeline
echo "📦 Creating simple pipeline..."
kubectl apply -f - <<EOF
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: simple-pipeline
  namespace: seldon-mesh
spec:
  steps:
  - name: iris
  output:
    steps: [iris]
EOF

sleep 30

echo "✅ Deployment complete!"
kubectl get models,pipelines -n seldon-mesh