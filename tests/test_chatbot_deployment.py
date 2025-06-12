#!/usr/bin/env python3
"""
Live test script for chatbot MLOps deployment
"""

import subprocess
import json
import time
import requests
import sys

def run_cmd(cmd):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result

def log(msg):
    print(f"✅ {msg}")

def error(msg):
    print(f"❌ {msg}")
    
def test_deployment():
    namespace = "chatbot-test"
    
    # Step 1: Create namespace
    log("Creating test namespace...")
    run_cmd(f"kubectl create namespace {namespace} --dry-run=client -o yaml | kubectl apply -f -")
    run_cmd(f"kubectl label namespace {namespace} istio-injection=enabled --overwrite")
    
    # Step 2: Check gateway
    log("Checking Istio gateway...")
    result = run_cmd("kubectl get svc istio-ingressgateway -n istio-system -o json")
    gateway_ip = None
    if result.stdout:
        try:
            svc_data = json.loads(result.stdout)
            ingress = svc_data.get("status", {}).get("loadBalancer", {}).get("ingress", [])
            if ingress and ingress[0].get("ip"):
                gateway_ip = ingress[0].get("ip")
                log(f"Gateway IP: {gateway_ip}")
            else:
                error("No gateway IP found")
        except:
            error("Failed to parse gateway service")
    
    # Step 3: Deploy a test server
    log("Deploying MLServer...")
    server_yaml = f"""apiVersion: mlops.seldon.io/v1alpha1
kind: Server
metadata:
  name: test-mlserver
  namespace: {namespace}
spec:
  replicas: 2
  serverConfig: mlserver
"""
    
    with open("/tmp/test-server.yaml", "w") as f:
        f.write(server_yaml)
    
    result = run_cmd(f"kubectl apply -f /tmp/test-server.yaml")
    if result.returncode != 0:
        error("Failed to create server")
        return
    
    # Wait for server to be ready
    log("Waiting for server to be ready...")
    for i in range(30):
        result = run_cmd(f"kubectl get server test-mlserver -n {namespace} -o json")
        if result.stdout:
            try:
                server = json.loads(result.stdout)
                if server.get("status", {}).get("state") == "Ready":
                    log("Server is ready!")
                    break
            except:
                pass
        time.sleep(5)
        print(f"Waiting... {i*5}s")
    
    # Step 4: Deploy a test model
    log("Deploying test model...")
    model_yaml = f"""apiVersion: mlops.seldon.io/v1alpha1
kind: Model
metadata:
  name: test-intent-classifier
  namespace: {namespace}
spec:
  storageUri: gs://seldon-models/scv2/samples/mlserver_1.5.0/iris-sklearn
  requirements: ["sklearn"]
  memory: 500Mi
"""
    
    with open("/tmp/test-model.yaml", "w") as f:
        f.write(model_yaml)
    
    result = run_cmd(f"kubectl apply -f /tmp/test-model.yaml")
    if result.returncode != 0:
        error("Failed to create model")
        return
    
    # Wait for model
    log("Waiting for model to be ready...")
    for i in range(60):
        result = run_cmd(f"kubectl get model test-intent-classifier -n {namespace} -o json")
        if result.stdout:
            try:
                model = json.loads(result.stdout)
                if model.get("status", {}).get("state") == "Ready":
                    log("Model is ready!")
                    break
            except:
                pass
        time.sleep(5)
        print(f"Waiting... {i*5}s")
    
    # Step 5: Check pods
    log("Checking pods...")
    run_cmd(f"kubectl get pods -n {namespace}")
    
    # Step 6: Test inference
    if gateway_ip:
        log("Testing inference...")
        url = f"http://{gateway_ip}/v2/models/test-intent-classifier/infer"
        payload = {
            "inputs": [{
                "name": "predict",
                "shape": [1, 4],
                "datatype": "FP32",
                "data": [[5.1, 3.5, 1.4, 0.2]]
            }]
        }
        headers = {
            "Content-Type": "application/json",
            "Seldon-Model": "test-intent-classifier",
            "Host": f"{namespace}.inference.seldon.test"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                log("Inference successful!")
                print(json.dumps(response.json(), indent=2))
            else:
                error(f"Inference failed: {response.status_code}")
                print(response.text)
        except Exception as e:
            error(f"Request failed: {e}")
    
    # Step 7: Check logs
    log("Checking model logs...")
    run_cmd(f"kubectl logs -n {namespace} -l model.seldon.io/name=test-intent-classifier --tail=20")
    
    # Cleanup option
    cleanup = input("\nClean up test resources? (y/N): ").strip().lower()
    if cleanup == 'y':
        log("Cleaning up...")
        run_cmd(f"kubectl delete namespace {namespace}")
    else:
        log(f"Resources preserved in namespace: {namespace}")

if __name__ == "__main__":
    test_deployment()