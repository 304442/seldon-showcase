#!/usr/bin/env python3
"""
Working inference example for Seldon Core 2
"""

import requests
import json
import time

# Test all deployed models
models = [
    "iris",
    "sklearn-iris", 
    "sklearn-iris-v2",
    "feature-transformer",
    "product-classifier-v1",
    "product-classifier-v2",
    "intent-classifier-v1",
    "entity-extractor",
    "product-recommender",
    "drift-detector",
    "model-explainer",
    "performance-monitor"
]

gateway_ip = "34.90.187.46"
gateway_port = "80"

print("🧪 Testing Seldon Model Inference")
print("=" * 50)

working_models = []
failed_models = []

for model in models:
    url = f"http://{gateway_ip}:{gateway_port}/v2/models/{model}/infer"
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
        "Seldon-Model": model
    }
    
    try:
        start = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            print(f"✅ {model}: SUCCESS ({latency:.1f}ms)")
            working_models.append(model)
        else:
            print(f"❌ {model}: FAILED (HTTP {response.status_code})")
            failed_models.append(model)
    except Exception as e:
        print(f"❌ {model}: ERROR ({str(e)})")
        failed_models.append(model)

print("\n📊 Summary:")
print(f"Working models: {len(working_models)}/{len(models)}")
print(f"Success rate: {len(working_models)/len(models)*100:.1f}%")

if working_models:
    print(f"\n✅ Working models: {', '.join(working_models)}")
if failed_models:
    print(f"\n❌ Failed models: {', '.join(failed_models)}")

# Test a pipeline if any models work
if "feature-transformer" in working_models:
    print("\n🔗 Testing Pipeline Inference")
    print("=" * 50)
    
    pipelines = ["product-pipeline-v1", "product-pipeline-v2", "instant-chatbot"]
    
    for pipeline in pipelines:
        url = f"http://{gateway_ip}:{gateway_port}/v2/models/{pipeline}/infer"
        headers = {
            "Content-Type": "application/json",
            "Seldon-Model": f"{pipeline}.pipeline"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ {pipeline}: SUCCESS")
            else:
                print(f"❌ {pipeline}: FAILED (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ {pipeline}: ERROR ({str(e)})")

print("\n✨ Test complete!")