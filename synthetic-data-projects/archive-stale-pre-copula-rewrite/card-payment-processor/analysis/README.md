# SDLC Performance Prediction System - Card Payment Processor

A comprehensive machine learning pipeline for predicting payment system performance metrics (transaction success rate, system uptime, fraud detection rate) based on Software Development Life Cycle (SDLC) metrics for card payment processing platforms.

## 📋 Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Execution Steps](#detailed-execution-steps)
- [File Structure](#file-structure)
- [Configuration](#configuration)
- [API Usage](#api-usage)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This system predicts next release performance for a card payment processing platform using historical SDLC metrics including:
- **Input Metrics**: Build success rates, test coverage, code quality, security scan results, PCI DSS compliance
- **Target Predictions**: Transaction success rate (%), system uptime (%), fraud detection rate (%), payment processing accuracy (%)
- **ML Models**: Random Forest, Gradient Boosting, Linear Regression, Ridge, Lasso
- **Payment-Specific Focus**: Financial compliance, security metrics, transaction processing reliability

## 🔧 Prerequisites

### Software Requirements
- **Python 3.8+**
- **Jupyter Notebook** (for interactive analysis)
- **Git** (optional, for version control)

### Python Libraries
```bash
pip install pandas numpy scikit-learn matplotlib seaborn
pip install jupyter joblib
pip install flask  # For API deployment
pip install shap   # For model interpretability (optional)
```

## 📦 Installation

1. **Clone or Download the Project**
   ```bash
   git clone <repository-url>
   cd Predicting-Software-System-Performance/code/projects/card-payment-processor/analysis
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Option 1: Complete Pipeline (Recommended)
```bash
# Execute the entire pipeline
python model_training.py
```

### Option 2: Interactive Analysis
```bash
# Launch Jupyter notebook for interactive exploration
jupyter notebook analysis.ipynb
```

### Option 3: Step-by-step Execution
```bash
# 1. Feature engineering
python feature_analysis.py

# 2. Train models
python model_training.py

# 3. Evaluate performance
python model_evaluation.py

# 4. Deploy model
python deploy_model.py
```

## 📊 Detailed Execution Steps

### Step 1: Data Loading and Exploration
The system automatically loads payment processing SDLC data from CSV files:
- Requirements metrics (PCI DSS compliance, security requirements)
- Test metrics (security testing, fraud detection validation)
- UAT metrics (business process validation, compliance verification)
- Production metrics (transaction success, fraud detection effectiveness)
- Build metrics (security scanning, compliance validation)
- Code metrics (security hotspots, vulnerabilities)
- Chaos testing metrics (payment gateway resilience)
- Performance metrics (payment authorization latency, throughput)

### Step 2: Feature Engineering
- Creates derived features from payment-specific SDLC metrics
- Implements lag features for temporal dependencies
- Calculates rolling averages for stability metrics
- Handles missing values and outliers specific to payment processing

### Step 3: Model Training
Trains multiple ML models optimized for payment system predictions:
- **Random Forest**: For non-linear payment pattern recognition
- **Gradient Boosting**: For complex payment metric interactions
- **Linear Regression**: For baseline payment performance prediction
- **Ridge/Lasso**: For regularized payment feature selection

### Step 4: Model Evaluation
- Cross-validation with payment-specific metrics
- Feature importance analysis for financial compliance
- Model performance comparison for transaction prediction
- Error analysis focusing on payment failure scenarios

### Step 5: Prediction Pipeline
- Real-time payment performance prediction
- Batch processing for release planning
- API endpoint for integration with payment systems
- Automated model retraining based on payment data

## 📁 File Structure

```
analysis/
├── analysis.ipynb              # Interactive Jupyter notebook for payment analysis
├── feature_analysis.py         # Payment-specific feature engineering
├── feature_engineering.ipynb   # Interactive feature exploration for payments
├── model_training.py           # ML model training for payment predictions
├── model_evaluation.py         # Payment model performance evaluation
├── model_comparison.ipynb      # Interactive model comparison for payments
├── prediction_pipeline.py      # Payment prediction pipeline
├── deploy_model.py            # Payment model deployment
├── model_monitoring.py        # Payment model monitoring and alerts
├── requirements.txt           # Python dependencies for payment system
├── README.md                  # This comprehensive guide
└── config/
    ├── model_config.json      # Payment model configuration
    └── deployment_config.json # Payment deployment settings
```

## ⚙️ Configuration

### Model Configuration (`model_config.json`)
```json
{
  "target_variables": [
    "Transaction Success Rate (%)",
    "System Uptime (%)", 
    "Fraud Detection Rate (%)",
    "Payment Processing Accuracy (%)"
  ],
  "models": {
    "random_forest": {"n_estimators": 100, "random_state": 42},
    "gradient_boosting": {"n_estimators": 100, "learning_rate": 0.1},
    "linear_regression": {},
    "ridge": {"alpha": 1.0},
    "lasso": {"alpha": 1.0}
  },
  "payment_features": {
    "security_metrics": ["Security Scan Pass Rate (%)", "PCI DSS Test Coverage (%)"],
    "compliance_metrics": ["Compliance Score (1-10)", "Regulatory Compliance Validation (%)"],
    "performance_metrics": ["Transaction Authorization Time (ms)", "Payment Processing Latency (ms)"]
  }
}
```

## 🔌 API Usage

### Start the Payment Prediction API
```bash
python deploy_model.py
```

### API Endpoints

#### 1. Single Payment Release Prediction
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "build_success_rate": 95.5,
    "security_scan_pass_rate": 98.2,
    "pci_dss_compliance": 99.1,
    "fraud_detection_test_coverage": 94.8,
    "transaction_test_coverage": 96.7
  }'
```

#### 2. Batch Payment Predictions
```bash
curl -X POST http://localhost:5000/predict_batch \
  -H "Content-Type: application/json" \
  -d '{
    "releases": [
      {"build_success_rate": 95.5, "security_scan_pass_rate": 98.2},
      {"build_success_rate": 92.1, "security_scan_pass_rate": 95.8}
    ]
  }'
```

#### 3. Payment Model Health Check
```bash
curl http://localhost:5000/health
```

#### 4. Payment Feature Importance
```bash
curl http://localhost:5000/feature_importance
```

## 📈 Monitoring

### Real-time Payment Monitoring
```bash
python model_monitoring.py
```

This provides:
- **Payment Model Drift Detection**: Monitors changes in transaction patterns
- **Performance Alerts**: Notifications for payment system degradation
- **Compliance Monitoring**: Tracks PCI DSS and regulatory compliance
- **Security Alerts**: Monitors fraud detection effectiveness
- **Transaction Monitoring**: Real-time payment success rate tracking

### Key Payment Metrics Monitored
- Transaction success rate predictions vs. actual
- Payment processing latency predictions
- Fraud detection accuracy trends
- PCI DSS compliance score tracking
- Security incident prediction accuracy

## 🔧 Troubleshooting

### Common Payment-Specific Issues

#### 1. Payment Data Loading Issues
```bash
# Check payment data files
ls -la ../synthetic-data/
# Verify payment CSV structure
python -c "import pandas as pd; print(pd.read_csv('../synthetic-data/production_run_metrics.csv').head())"
```

#### 2. Security Compliance Errors
- Ensure PCI DSS compliance metrics are properly formatted
- Verify security scan results are within expected ranges
- Check fraud detection metrics for anomalies

#### 3. Payment Model Performance Issues
- Review transaction-specific feature engineering
- Validate payment processing metrics quality
- Check for payment seasonal patterns in data

#### 4. Payment API Deployment Issues
```bash
# Test payment model loading
python -c "import joblib; model = joblib.load('best_model.pkl'); print('Payment model loaded successfully')"

# Check payment API configuration
python -c "import json; print(json.load(open('deployment_config.json')))"
```

### Performance Optimization for Payment Systems

1. **Memory Usage**: Payment models handle large transaction datasets
2. **Prediction Latency**: Optimize for real-time payment authorization
3. **Batch Processing**: Efficient processing of payment batch predictions
4. **Security**: Ensure payment data encryption and secure API endpoints

### Support and Payment System Integration

For payment-specific support:
1. Check payment data quality and compliance requirements
2. Validate PCI DSS compliance in predictions
3. Monitor fraud detection model performance
4. Ensure payment API security standards
5. Review transaction processing accuracy metrics

## 📚 Additional Resources

- **Payment Industry Standards**: PCI DSS compliance guidelines
- **Financial Regulations**: Payment processing regulatory requirements
- **Security Best Practices**: Payment system security implementation
- **Performance Benchmarks**: Payment industry performance standards

---

**Note**: This system is designed specifically for card payment processing platforms and includes specialized metrics for financial compliance, security, and transaction processing reliability.