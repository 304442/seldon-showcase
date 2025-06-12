#!/bin/bash

echo "Deploying all pipelines..."

# Core pipelines for v71.ipynb
cat <<EOF | kubectl apply -f -
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
EOF

# Chatbot pipelines
cat <<EOF | kubectl apply -f -
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
  output:
    steps: [entity-extractor]
EOF

# Monitoring pipelines
cat <<EOF | kubectl apply -f -
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
  output:
    steps: [model-explainer]
EOF

echo "All pipelines deployed. Checking status..."
kubectl get pipelines -n seldon-mesh