#!/bin/bash
set -e

echo "🚀 Final deployment of all Seldon Showcase models..."

# Deploy all models
kubectl apply -f - <<EOF
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: feature-transformer
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: product-classifier-v1
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: product-classifier-v2
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: intent-classifier-v1
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: entity-extractor
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: product-recommender
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: drift-detector
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: model-explainer
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: performance-monitor
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
EOF

echo "⏳ Waiting for models to be ready..."
sleep 60

echo "📊 Model status:"
kubectl get models -n seldon-mesh

# Deploy all pipelines
echo "📦 Deploying pipelines..."
kubectl apply -f - <<EOF
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: product-pipeline-v1
  namespace: seldon-mesh
spec:
  steps:
  - name: feature-transformer
  - name: product-classifier-v1
    inputs: [feature-transformer.outputs]
  output:
    steps: [product-classifier-v1]
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: product-pipeline-v2
  namespace: seldon-mesh
spec:
  steps:
  - name: feature-transformer
  - name: product-classifier-v2
    inputs: [feature-transformer.outputs]
  output:
    steps: [product-classifier-v2]
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: instant-chatbot
  namespace: seldon-mesh
spec:
  steps:
  - name: intent-classifier-v1
  output:
    steps: [intent-classifier-v1]
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: chatbot-with-recommendations
  namespace: seldon-mesh
spec:
  steps:
  - name: intent-classifier-v1
  - name: entity-extractor
    inputs: [intent-classifier-v1.outputs]
  - name: product-recommender
    inputs: [entity-extractor.outputs]
  output:
    steps: [product-recommender]
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: real-time-monitoring
  namespace: seldon-mesh
spec:
  steps:
  - name: drift-detector
  - name: model-explainer
    inputs: [drift-detector.outputs]
  - name: performance-monitor
    inputs: [model-explainer.outputs]
  output:
    steps: [performance-monitor]
EOF

sleep 30

echo "📊 Pipeline status:"
kubectl get pipelines -n seldon-mesh

# Deploy experiment
echo "🧪 Deploying A/B test experiment..."
kubectl apply -f - <<EOF
apiVersion: mlops.seldon.io/v1alpha1
kind: Experiment
metadata:
  name: product-ab-test
  namespace: seldon-mesh
spec:
  default: product-pipeline-v1
  resourceType: pipeline
  candidates:
  - name: product-pipeline-v1
    weight: 90
  - name: product-pipeline-v2
    weight: 10
EOF

echo "✅ All components deployed!"