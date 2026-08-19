# SDLC Performance Prediction System - XYZ Sales Force

A comprehensive machine learning pipeline for predicting software system performance metrics (uptime, response time, customer satisfaction) based on Software Development Life Cycle (SDLC) metrics.

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

This system predicts next release performance using historical SDLC metrics including:
- **Input Metrics**: Build success rates, test coverage, code quality, requirements defects
- **Target Predictions**: System uptime (%), customer satisfaction, response times
- **ML Models**: Random Forest, Gradient Boosting, Linear Regression, Ridge, Lasso

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
   cd Predicting-Software-System-Performance/code/projects/xyz-sales-force/analysis
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If requirements.txt doesn't exist, install packages manually as listed above*

3. **Verify Installation**
   ```bash
   python -c "import pandas, numpy, sklearn; print('All dependencies installed successfully!')"
   ```

## ⚡ Quick Start

For a rapid demonstration:

```bash
# 1. Run feature engineering
jupyter notebook feature_engineering.ipynb

# 2. Train models
python model_training.py

# 3. Compare models and select best
jupyter notebook model_comparison.ipynb

# 4. Deploy the model
python deploy_model.py
```

## 📖 Detailed Execution Steps

### Step 1: Data Preparation and Feature Engineering

**File**: `feature_engineering.ipynb`

1. **Open Jupyter Notebook**
   ```bash
   jupyter notebook feature_engineering.ipynb
   ```

2. **Execute All Cells** (Ctrl+A, then Shift+Enter)
   - Loads SDLC metrics data from `../synthetic-data/` directory
   - Creates rolling window features (3, 5, 7, 10 periods)
   - Generates lag features (1, 2, 3, 5 periods)
   - Engineers cross-phase metrics
   - Applies categorical encoding
   - Performs time-based train/test split

3. **Expected Outputs**
   - `engineered_features.pkl` - Processed dataset
   - Feature statistics and visualizations
   - Data summary report

**⏱️ Estimated Time**: 5-10 minutes

### Step 2: Model Training

**File**: `model_training.py`

1. **Run Training Script**
   ```bash
   python model_training.py
   ```

2. **What It Does**
   - Loads engineered features
   - Trains 5 different ML models
   - Performs time-series cross-validation
   - Evaluates models on test set
   - Saves best model

3. **Expected Outputs**
   ```
   Training models...
     Training linear_regression...
     ✓ linear_regression trained successfully
     Training ridge_regression...
     ✓ ridge_regression trained successfully
     [... other models ...]
   
   Evaluating models...
     linear_regression: RMSE=2.156, MAE=1.672, R²=0.234
     [... other results ...]
   
   Best model (random_forest) saved to best_model.pkl
   ```

**⏱️ Estimated Time**: 2-5 minutes

### Step 3: Model Comparison and Selection

**File**: `model_comparison.ipynb`

1. **Open Comparison Notebook**
   ```bash
   jupyter notebook model_comparison.ipynb
   ```

2. **Execute All Cells**
   - Loads and trains multiple models
   - Generates comprehensive performance comparison
   - Creates prediction visualizations
   - Analyzes residuals and feature importance
   - Selects best model for deployment

3. **Expected Outputs**
   - Model performance comparison tables
   - Prediction vs actual scatter plots
   - Residual analysis plots
   - Feature importance charts
   - `best_model_comparison.pkl` - Production-ready model

**⏱️ Estimated Time**: 5-8 minutes

### Step 4: Model Deployment

**File**: `deploy_model.py`

1. **Deploy Model**
   ```bash
   python deploy_model.py
   ```

2. **Interactive Setup**
   ```
   SDLC Performance Prediction - Deployment & Monitoring
   ============================================================
   ✓ Created deployment configuration
   ✓ Model deployment successful
   ✓ Test prediction successful: 97.85%
   
   📊 Generating monitoring report...
   
   🚀 Deployment complete!
   
   Start API server now? (y/n): y
   ```

3. **API Server** (if started)
   ```
   Starting API server on 127.0.0.1:5000
   * Running on http://127.0.0.1:5000
   ```

**⏱️ Estimated Time**: 2-3 minutes

### Step 5: Feature Analysis (Optional)

**File**: `feature_analysis.py`

1. **Run Feature Analysis**
   ```bash
   python feature_analysis.py
   ```

2. **Outputs**
   - Feature importance rankings
   - SHAP analysis (if SHAP installed)
   - Correlation analysis
   - Feature analysis report

**⏱️ Estimated Time**: 3-5 minutes

### Step 6: Monitoring Setup

**File**: `model_monitoring.py`

1. **Run Monitoring**
   ```bash
   python model_monitoring.py
   ```

2. **Outputs**
   - Monitoring dashboard (`monitoring_dashboard.html`)
   - Performance tracking report
   - Alert system status

**⏱️ Estimated Time**: 1-2 minutes

## 📁 File Structure

```
analysis/
├── README.md                      # This file
├── feature_engineering.ipynb      # Step 1: Data preparation
├── model_training.py              # Step 2: Model training
├── model_comparison.ipynb         # Step 3: Model comparison
├── prediction_pipeline.py         # Prediction pipeline class
├── feature_analysis.py            # Step 5: Feature analysis
├── deploy_model.py                # Step 4: Deployment
├── model_monitoring.py            # Step 6: Monitoring
├── model_evaluation.py            # Model evaluation utilities
├── use_model_example.py           # Example usage script
├── IMPLEMENTATION_SUMMARY.md      # Technical documentation
└── USAGE_GUIDE.md                 # User guide
└── todo.md                        # Project roadmap

Generated Files:
├── engineered_features.pkl        # Processed data
├── best_model.pkl                 # Trained model
├── best_model_comparison.pkl      # Production model
├── deployment_config.json         # Deployment settings
├── deployment_info.json           # Deployment metadata
├── monitoring_dashboard.html      # Monitoring interface
├── feature_analysis_report.txt    # Feature analysis
└── *.log                          # Log files
```

## ⚙️ Configuration

### Deployment Configuration
Edit `deployment_config.json`:
```json
{
  "api_host": "127.0.0.1",
  "api_port": 5000,
  "debug": true,
  "log_predictions": true,
  "monitoring_enabled": true
}
```

### Monitoring Configuration
Create `monitoring_config.json`:
```json
{
  "performance_threshold": 0.7,
  "drift_threshold": 0.15,
  "prediction_volume_threshold": 10,
  "alert_email": "your-email@example.com"
}
```

## 🌐 API Usage

Once deployed, the API provides several endpoints:

### Health Check
```bash
curl http://localhost:5000/health
```

### Single Prediction
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Build Success Rate (%)": 88.0,
    "Test Coverage (%)": 82.0,
    "Overall Test Pass Rate (%)": 94.0,
    "Customer Satisfaction Score (1-10)": 8.5,
    "Average Response Time (ms)": 180.0
  }'
```

### Batch Predictions
```bash
curl -X POST http://localhost:5000/batch_predict \
  -H "Content-Type: application/json" \
  -d '{
    "batch": [
      {"Build Success Rate (%)": 88.0, "Test Coverage (%)": 82.0},
      {"Build Success Rate (%)": 92.0, "Test Coverage (%)": 85.0}
    ]
  }'
```

### Model Information
```bash
curl http://localhost:5000/model/info
```

## 📊 Monitoring

### Real-time Monitoring
1. **Start API Server**
   ```bash
   python deploy_model.py --start-server
   ```

2. **Run Monitoring** (in separate terminal)
   ```bash
   python deploy_model.py --monitor
   ```

3. **View Dashboard**
   Open `monitoring_dashboard.html` in web browser

### Automated Monitoring
Set up a cron job for regular monitoring:
```bash
# Add to crontab (crontab -e)
0 */6 * * * cd /path/to/analysis && python model_monitoring.py
```

## 🔧 Troubleshooting

### Common Issues

1. **"ModuleNotFoundError" for dependencies**
   ```bash
   pip install pandas numpy scikit-learn matplotlib seaborn jupyter
   ```

2. **"FileNotFoundError" for data files**
   - Ensure you're in the correct directory
   - Check if `../synthetic-data/` directory exists
   - Verify data files are present

3. **"Model not found" errors**
   - Run steps in order (feature engineering → training → comparison)
   - Check if `.pkl` files were generated

4. **API server won't start**
   ```bash
   pip install flask
   # Check if port 5000 is available
   netstat -an | find "5000"
   ```

5. **SHAP errors (optional)**
   ```bash
   pip install shap
   # If installation fails, SHAP features will be skipped
   ```

### Performance Issues

1. **Slow execution**
   - Reduce dataset size for testing
   - Limit cross-validation folds
   - Use fewer features

2. **Memory issues**
   - Close other applications
   - Reduce batch sizes
   - Use sampling for large datasets

3. **Poor model performance**
   - Check data quality
   - Increase training data
   - Tune hyperparameters

### Getting Help

1. **Check log files** (`*.log`) for error details
2. **Review generated reports** for insights
3. **Verify data integrity** in feature engineering step
4. **Ensure all prerequisites** are installed

## 📈 Expected Results

### Model Performance
- **R² Score**: 0.7 - 0.9 (Good to Excellent)
- **RMSE**: 1.0 - 3.0 (depending on data scale)
- **MAE**: 0.8 - 2.5 (depending on data scale)

### Prediction Accuracy
- **System Uptime**: ±2-5% prediction error
- **Response Time**: ±10-20% prediction error
- **Customer Satisfaction**: ±0.5-1.0 point error

### Feature Importance
Top predictive features typically include:
- Previous release performance metrics
- Test coverage and pass rates
- Build success rates
- Code quality indicators

---

## 🚀 Next Steps

After successful execution:
1. **Integrate with CI/CD** pipeline for automated predictions
2. **Set up monitoring alerts** for production use
3. **Collect actual outcomes** for model validation
4. **Schedule periodic retraining** to maintain accuracy
5. **Expand to additional target metrics** as needed

For questions or issues, refer to `IMPLEMENTATION_SUMMARY.md` for technical details.