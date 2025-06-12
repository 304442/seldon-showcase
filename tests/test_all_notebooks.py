#!/usr/bin/env python3
"""
Live testing script for all Seldon Core 2 notebooks
Tests deployment, inference, monitoring, and cleanup
Note: Notebooks are now in the notebooks/ directory
"""

import subprocess
import json
import time
import requests
import sys
from datetime import datetime

class SeldonNotebookTester:
    def __init__(self):
        self.namespace = "seldon-mesh"
        self.gateway_ip = None
        self.gateway_port = "80"
        self.test_results = {
            "infrastructure": {},
            "models": {},
            "pipelines": {},
            "monitoring": {},
            "performance": {}
        }
        
    def run_cmd(self, cmd):
        """Execute command and return result"""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result
    
    def log(self, msg, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        print(f"{icons.get(level, '📝')} [{timestamp}] {msg}")
    
    def test_prerequisites(self):
        """Test all prerequisites"""
        self.log("Testing prerequisites...")
        
        # Check kubectl
        result = self.run_cmd("kubectl version --client -o json")
        self.test_results["infrastructure"]["kubectl"] = result.returncode == 0
        
        # Check Seldon CRDs
        crds = ["servers", "models", "pipelines", "experiments"]
        crd_count = 0
        for crd in crds:
            result = self.run_cmd(f"kubectl get crd {crd}.mlops.seldon.io")
            if result.returncode == 0:
                crd_count += 1
        
        self.test_results["infrastructure"]["seldon_crds"] = crd_count == len(crds)
        self.log(f"Found {crd_count}/{len(crds)} Seldon CRDs", "INFO")
        
        # Check namespace
        result = self.run_cmd(f"kubectl get namespace {self.namespace}")
        self.test_results["infrastructure"]["namespace"] = result.returncode == 0
        
        # Check Istio
        result = self.run_cmd("kubectl get ns istio-system")
        self.test_results["infrastructure"]["istio"] = result.returncode == 0
        
        # Get gateway IP
        result = self.run_cmd("kubectl get svc istio-ingressgateway -n istio-system -o json")
        if result.returncode == 0 and result.stdout:
            try:
                svc_data = json.loads(result.stdout)
                ingress = svc_data.get("status", {}).get("loadBalancer", {}).get("ingress", [])
                if ingress and ingress[0].get("ip"):
                    self.gateway_ip = ingress[0].get("ip")
                    self.log(f"Gateway IP: {self.gateway_ip}", "SUCCESS")
            except:
                pass
        
        if not self.gateway_ip:
            self.log("No gateway IP found - trying localhost", "WARNING")
            self.gateway_ip = "localhost"
        
        return all(self.test_results["infrastructure"].values())
    
    def test_servers(self):
        """Test server deployments"""
        self.log("Testing servers...")
        
        servers = ["mlserver", "triton"]
        for server in servers:
            result = self.run_cmd(f"kubectl get server {server} -n {self.namespace} -o json")
            if result.returncode == 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # Check the Ready condition instead of state
                    ready = data.get("status", {}).get("conditions", [])
                    is_ready = any(c.get("type") == "Ready" and c.get("status") == "True" for c in ready)
                    self.test_results["infrastructure"][f"server_{server}"] = is_ready
                    self.log(f"Server {server}: {'Ready' if is_ready else 'Not Ready'}", "INFO")
                except:
                    self.test_results["infrastructure"][f"server_{server}"] = False
            else:
                self.test_results["infrastructure"][f"server_{server}"] = False
    
    def test_model_inference(self, model_name):
        """Test individual model inference"""
        url = f"http://{self.gateway_ip}:{self.gateway_port}/v2/models/{model_name}/infer"
        payload = {
            "inputs": [{
                "name": "predict",
                "shape": [1, 4],
                "datatype": "FP32",
                "data": [[5.1, 3.5, 1.4, 0.2]]
            }]
        }
        headers = {"Content-Type": "application/json", "Seldon-Model": model_name}
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                self.test_results["models"][model_name] = {
                    "status": "success",
                    "latency_ms": round(latency, 1)
                }
                self.log(f"Model {model_name}: ✅ ({latency:.1f}ms)", "SUCCESS")
                return True
            else:
                self.test_results["models"][model_name] = {
                    "status": f"failed_{response.status_code}",
                    "error": response.text[:100]
                }
                self.log(f"Model {model_name}: ❌ ({response.status_code})", "ERROR")
                return False
        except Exception as e:
            self.test_results["models"][model_name] = {
                "status": "error",
                "error": str(e)
            }
            self.log(f"Model {model_name}: ❌ ({str(e)})", "ERROR")
            return False
    
    def test_pipeline_inference(self, pipeline_name):
        """Test pipeline inference"""
        url = f"http://{self.gateway_ip}:{self.gateway_port}/v2/models/{pipeline_name}/infer"
        payload = {
            "inputs": [{
                "name": "predict",
                "shape": [1, 4],
                "datatype": "FP32",
                "data": [[5.9, 3.0, 5.1, 1.8]]
            }]
        }
        headers = {
            "Content-Type": "application/json",
            "Seldon-Model": f"{pipeline_name}.pipeline"
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                self.test_results["pipelines"][pipeline_name] = {
                    "status": "success",
                    "latency_ms": round(latency, 1)
                }
                self.log(f"Pipeline {pipeline_name}: ✅ ({latency:.1f}ms)", "SUCCESS")
                return True
            else:
                self.test_results["pipelines"][pipeline_name] = {
                    "status": f"failed_{response.status_code}"
                }
                self.log(f"Pipeline {pipeline_name}: ❌ ({response.status_code})", "ERROR")
                return False
        except Exception as e:
            self.test_results["pipelines"][pipeline_name] = {
                "status": "error",
                "error": str(e)
            }
            self.log(f"Pipeline {pipeline_name}: ❌ ({str(e)})", "ERROR")
            return False
    
    def test_v71_notebook(self):
        """Test components from v71.ipynb"""
        self.log("\n=== Testing v71.ipynb Components ===", "INFO")
        
        # Test servers
        self.test_servers()
        
        # Test models
        models = ["feature-transformer", "product-classifier-v1", "product-classifier-v2"]
        for model in models:
            # Check if model exists
            result = self.run_cmd(f"kubectl get model {model} -n {self.namespace}")
            if result.returncode == 0:
                self.test_model_inference(model)
        
        # Test pipelines
        pipelines = ["product-pipeline-v1", "product-pipeline-v2"]
        for pipeline in pipelines:
            result = self.run_cmd(f"kubectl get pipeline {pipeline} -n {self.namespace}")
            if result.returncode == 0:
                self.test_pipeline_inference(pipeline)
        
        # Test experiment
        result = self.run_cmd(f"kubectl get experiment product-ab-test -n {self.namespace}")
        self.test_results["infrastructure"]["ab_test"] = result.returncode == 0
    
    def test_chatbot_notebook(self):
        """Test components from chatbot notebook"""
        self.log("\n=== Testing Chatbot Components ===", "INFO")
        
        # Test chatbot models
        models = ["intent-classifier-v1", "entity-extractor", "product-recommender"]
        for model in models:
            result = self.run_cmd(f"kubectl get model {model} -n {self.namespace}")
            if result.returncode == 0:
                self.test_model_inference(model)
        
        # Test chatbot pipelines
        pipelines = ["instant-chatbot", "chatbot-with-recommendations"]
        for pipeline in pipelines:
            result = self.run_cmd(f"kubectl get pipeline {pipeline} -n {self.namespace}")
            if result.returncode == 0:
                self.test_pipeline_inference(pipeline)
    
    def test_monitoring_notebook(self):
        """Test monitoring components"""
        self.log("\n=== Testing Monitoring Components ===", "INFO")
        
        # Test monitoring models
        models = ["drift-detector", "model-explainer", "performance-monitor"]
        for model in models:
            result = self.run_cmd(f"kubectl get model {model} -n {self.namespace}")
            if result.returncode == 0:
                self.test_model_inference(model)
        
        # Test monitoring pipelines
        pipelines = ["real-time-monitoring", "explanation-service"]
        for pipeline in pipelines:
            result = self.run_cmd(f"kubectl get pipeline {pipeline} -n {self.namespace}")
            if result.returncode == 0:
                self.test_pipeline_inference(pipeline)
    
    def test_performance(self):
        """Test performance with concurrent requests"""
        self.log("\n=== Performance Testing ===", "INFO")
        
        # Test a deployed model with multiple requests
        test_model = None
        for model in ["product-classifier-v1", "intent-classifier-v1"]:
            result = self.run_cmd(f"kubectl get model {model} -n {self.namespace}")
            if result.returncode == 0:
                test_model = model
                break
        
        if not test_model:
            self.log("No model available for performance testing", "WARNING")
            return
        
        # Send 10 requests and measure latencies
        latencies = []
        for i in range(10):
            url = f"http://{self.gateway_ip}:{self.gateway_port}/v2/models/{test_model}/infer"
            payload = {
                "inputs": [{
                    "name": "predict",
                    "shape": [1, 4],
                    "datatype": "FP32",
                    "data": [[5.1, 3.5, 1.4, 0.2]]
                }]
            }
            
            try:
                start_time = time.time()
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                latency = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    latencies.append(latency)
            except:
                pass
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
            
            self.test_results["performance"] = {
                "requests": len(latencies),
                "avg_latency_ms": round(avg_latency, 1),
                "p95_latency_ms": round(p95_latency, 1),
                "success_rate": f"{len(latencies)/10*100:.0f}%"
            }
            
            self.log(f"Performance: {len(latencies)} requests, avg={avg_latency:.1f}ms, p95={p95_latency:.1f}ms", "INFO")
    
    def generate_report(self):
        """Generate test report"""
        self.log("\n=== Test Report ===", "INFO")
        
        # Infrastructure
        infra_pass = sum(1 for v in self.test_results["infrastructure"].values() if v)
        infra_total = len(self.test_results["infrastructure"])
        self.log(f"Infrastructure: {infra_pass}/{infra_total} passed", "INFO")
        
        # Models
        model_success = sum(1 for v in self.test_results["models"].values() if v.get("status") == "success")
        model_total = len(self.test_results["models"])
        self.log(f"Models: {model_success}/{model_total} working", "INFO")
        
        # Pipelines
        pipeline_success = sum(1 for v in self.test_results["pipelines"].values() if v.get("status") == "success")
        pipeline_total = len(self.test_results["pipelines"])
        self.log(f"Pipelines: {pipeline_success}/{pipeline_total} working", "INFO")
        
        # Performance
        if self.test_results["performance"]:
            perf = self.test_results["performance"]
            self.log(f"Performance: {perf['avg_latency_ms']}ms avg, {perf['p95_latency_ms']}ms p95", "INFO")
        
        # Save detailed report
        with open("test_report.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        self.log("Detailed report saved to test_report.json", "SUCCESS")
        
        # Overall status
        overall_success = (infra_pass > infra_total * 0.8 and 
                          model_success > 0 and 
                          pipeline_success > 0)
        
        if overall_success:
            self.log("\n✅ Overall: PASSED", "SUCCESS")
        else:
            self.log("\n❌ Overall: FAILED", "ERROR")
        
        return overall_success
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("Starting Seldon Core 2 notebook tests...", "INFO")
        
        # Test prerequisites
        if not self.test_prerequisites():
            self.log("Prerequisites not met - aborting tests", "ERROR")
            return False
        
        # Test each notebook's components
        self.test_v71_notebook()
        self.test_chatbot_notebook()
        self.test_monitoring_notebook()
        
        # Performance test
        self.test_performance()
        
        # Generate report
        return self.generate_report()

if __name__ == "__main__":
    tester = SeldonNotebookTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)