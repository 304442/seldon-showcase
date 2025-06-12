#!/usr/bin/env python3
"""
Deploy missing chatbot models from chatbot_mlops_showcase.ipynb
"""

import subprocess
import json
import time

def run(cmd, timeout=30):
    """Execute command"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))

def deploy_model(model_config):
    """Deploy a single model"""
    model_yaml = f"""apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: {model_config['name']}
  namespace: seldon-mesh
  labels:
    app: chatbot-platform
    component: {model_config['name']}
    version: v1
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements:
  - sklearn
  memory: {model_config.get('memory', '1Gi')}
"""
    
    with open(f"{model_config['name']}.yaml", "w") as f:
        f.write(model_yaml)
    
    print(f"Deploying {model_config['name']}...")
    result = run(f"kubectl apply -f {model_config['name']}.yaml")
    if result.returncode != 0:
        print(f"Failed to deploy {model_config['name']}: {result.stderr}")
        return False
    
    # Wait for model to be ready
    print(f"Waiting for {model_config['name']} to be ready...")
    for i in range(30):
        result = run(f"kubectl get model {model_config['name']} -n seldon-mesh -o jsonpath='{{.status.state}}'")
        if result.stdout.strip() == "ModelReady":
            print(f"✅ {model_config['name']} is ready")
            return True
        elif result.stdout.strip() == "ModelFailed":
            print(f"❌ {model_config['name']} failed")
            return False
        time.sleep(5)
    
    print(f"⚠️ {model_config['name']} deployment timeout")
    return False

# Chatbot models to deploy
chatbot_models = [
    {"name": "intent-classifier-v1", "memory": "500Mi"},
    {"name": "entity-extractor", "memory": "1Gi"},
    {"name": "product-recommender", "memory": "1Gi"},
]

# Deploy pipelines
def deploy_pipeline(pipeline_config):
    """Deploy a pipeline"""
    pipeline_yaml = f"""apiVersion: mlops.seldon.io/v1alpha1
kind: Pipeline
metadata:
  name: {pipeline_config['name']}
  namespace: seldon-mesh
  labels:
    app: chatbot-platform
spec:
  steps:
    - name: intent-classifier-v1
    - name: entity-extractor
      inputs: [{pipeline_config['name']}.inputs.text]
      tensorMap:
        {pipeline_config['name']}.inputs.text: text
    - name: product-recommender
      inputs: [{pipeline_config['name']}.inputs.text]
      tensorMap:
        {pipeline_config['name']}.inputs.text: text
  output:
    steps: [product-recommender]
"""
    
    with open(f"{pipeline_config['name']}.yaml", "w") as f:
        f.write(pipeline_yaml)
    
    print(f"Deploying pipeline {pipeline_config['name']}...")
    result = run(f"kubectl apply -f {pipeline_config['name']}.yaml")
    return result.returncode == 0

# Main deployment
print("🚀 Deploying Chatbot Components...")

# Check what's already deployed
existing_models = []
result = run("kubectl get models -n seldon-mesh -o json")
if result.returncode == 0 and result.stdout:
    try:
        models = json.loads(result.stdout)
        existing_models = [m["metadata"]["name"] for m in models.get("items", [])]
    except:
        pass

# Deploy missing models
deployed_count = 0
for model in chatbot_models:
    if model["name"] in existing_models:
        print(f"Model {model['name']} already exists")
        deployed_count += 1
    else:
        if deploy_model(model):
            deployed_count += 1

print(f"\n✅ Deployed {deployed_count}/{len(chatbot_models)} chatbot models")

# Deploy pipelines
pipelines = [
    {"name": "instant-chatbot"},
    {"name": "chatbot-with-recommendations"}
]

for pipeline in pipelines:
    if deploy_pipeline(pipeline):
        print(f"✅ Pipeline {pipeline['name']} deployed")
    else:
        print(f"❌ Pipeline {pipeline['name']} failed")

print("\nDeployment complete!")