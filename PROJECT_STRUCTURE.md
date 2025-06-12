# Project Structure 📁

```
Seldon-Showcase/
│
├── notebooks/                    # 📚 Jupyter notebooks (main deliverables)
│   ├── README.md                # Notebooks overview
│   ├── v71.ipynb                # Complete MLOps platform showcase
│   ├── chatbot_mlops_showcase.ipynb    # Real-time chatbot with recommendations
│   └── advanced_data_science_monitoring.ipynb  # ML monitoring suite
│
├── scripts/                      # 🔧 Deployment and utility scripts
│   ├── deploy-all-models.sh     # Deploy all models
│   ├── deploy-all-models-final.sh   # Final model deployment
│   ├── deploy-all-pipelines.sh     # Deploy all pipelines
│   └── deploy-everything-fresh.sh   # Complete fresh deployment
│
├── tests/                        # 🧪 Testing scripts
│   ├── test_all_notebooks.py    # Comprehensive test suite
│   ├── test_chatbot_deployment.py  # Chatbot-specific tests
│   ├── deploy-chatbot-models.py    # Chatbot model deployment
│   └── working-inference-example.py # Working inference examples
│
├── deployments/                  # 📦 Kubernetes manifests
│   ├── entity-extractor.yaml    # Entity extractor model
│   ├── feature-transformer-fix.yaml  # Feature transformer model
│   ├── feature-transformer-minimal.yaml
│   ├── intent-classifier-v1.yaml    # Intent classifier model
│   ├── monitoring-pipelines.yaml    # Monitoring pipelines
│   ├── performance-monitor.yaml     # Performance monitor model
│   ├── product-recommender.yaml     # Product recommender model
│   └── test-model.yaml             # Test model configuration
│
├── docs-gb/                      # 📖 Seldon documentation (reference)
│   └── [various .md files]      # Seldon Core 2 documentation
│
├── README.md                     # 🏠 Main project documentation
├── TESTING_SUMMARY.md           # 📊 Initial testing results
├── FINAL_TEST_RESULTS.md        # 📊 Final testing results
├── COMPLETE_TESTING_SUMMARY.md  # 📊 Complete autonomous testing summary
└── PROJECT_STRUCTURE.md         # 📁 This file
```

## 📂 Directory Descriptions

### `notebooks/`
The main deliverables - three production-ready Jupyter notebooks demonstrating Seldon Core 2 capabilities.

### `scripts/`
Bash scripts for deploying models, pipelines, and complete environments.

### `tests/`
Python scripts for testing deployments, inference endpoints, and validating functionality.

### `deployments/`
Kubernetes YAML manifests for individual model and pipeline deployments.

### `docs-gb/`
Reference documentation from Seldon for understanding the platform.

## 🚀 Quick Start

1. Start with the notebooks in `notebooks/`
2. Use scripts in `scripts/` for deployment
3. Validate with tests in `tests/`
4. Reference `deployments/` for individual resource definitions