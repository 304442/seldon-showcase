#!/bin/bash

echo "Deploying all models for Seldon Showcase..."

# Core models for v71.ipynb
cat <<EOF | kubectl apply -f -
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
EOF

echo "Waiting for core models..."
sleep 30

# Chatbot models
cat <<EOF | kubectl apply -f -
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
EOF

echo "Waiting for chatbot models..."
sleep 30

# Monitoring models - deploy on triton if mlserver is full
cat <<EOF | kubectl apply -f -
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: drift-detector
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/triton_23.10/cifar10-ensemble/resnet50
  requirements: []
---
apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: model-explainer
  namespace: seldon-mesh
spec:
  storageUri: gs://seldon-models/scv2/samples/triton_23.10/cifar10-ensemble/resnet50
  requirements: []
EOF

echo "All models deployed. Checking status..."
kubectl get models -n seldon-mesh