# ⚡ Auto-Analyst: Autonomous Data Analysis Pipeline

An end-to-end, serverless AI platform that automatically processes, cleans, and analyzes datasets to generate executive dashboards and business insights. Built with an event-driven AWS architecture and powered by Agentic LLM workflows.

![Auto-Analyst Dashboard Placeholder](https://via.placeholder.com/1200x600?text=Insert+Dashboard+Screenshot+Here)

## 🏗️ Architecture Overview

This project utilizes a decoupled, serverless architecture to handle heavy data processing asynchronously, ensuring a highly responsive frontend.

* **Frontend:** Streamlit (hosted on Streamlit Community Cloud)
* **Message Broker:** Amazon SQS (Simple Queue Service)
* **Storage:** Amazon S3 (Raw, Processed, Cleaned, and Report zones)
* **Compute Engine:** AWS Lambda (Python 3.10)
* **LLM Intelligence:** Groq API 
  * *Data Engineer Agent:* `llama-3.1-8b-instant` (Fast schema extraction & cleaning)
  * *Data Analyst Agent:* `llama-3.3-70b-versatile` (Deep reasoning & visualization strategy)

## ✨ Core Features

1. **Automated Data Preparation:** Upload raw CSVs; the system automatically extracts metadata and converts files to highly efficient Parquet formats.
2. **Agentic Data Cleaning:** A dedicated Data Engineer LLM writes and executes raw Pandas code to handle missing values, correct data types, and optimize the dataset without human intervention.
3. **Intelligent Visualization:** The Analyst Agent reads your stakeholder questions, selects the mathematically correct chart types (from 10+ Plotly variants), and generates the rendering code.
4. **Executive Summaries:** Automatically synthesizes data points into actionable, 3-5 sentence business conclusions.
5. **Fast "Re-Analyze":** Ask follow-up questions on the same dataset. The system intelligently skips the prepare/clean phases and jumps straight to analysis, returning new dashboards in seconds.

---

## 🚀 Deployment & Setup Guide

### Phase 1: AWS Backend Infrastructure

1. **Amazon S3:** Create a bucket (e.g., `auto-analyst-workspace`) to hold your data pipeline states (`raw/`, `processed/`, `cleaned/`, `reports/`).
2. **Amazon SQS:** Create a Standard SQS Queue (e.g., `AnalystJobQueue`) and copy the Queue URL.
3. **AWS Lambda:**
   * Create a Python 3.10 Lambda function (e.g., `AutoAnalystWorker`).
   * **Timeout:** Set to exactly 15 minutes.
   * **Memory:** Set to at least 1024 MB.
   * Add an **SQS Trigger** pointing to your queue.
   * Attach an IAM execution role with `AmazonS3FullAccess` and `AWSLambdaSQSQueueExecutionRole`.
4. **Lambda Dependencies (Layer):** * Compile a Lambda Layer containing `pandas`, `pyarrow`, and `groq` for `x86_64` architecture.
   * Attach this layer to your Lambda function.
5. **Environment Variables:**
   * Add `GROQ_API_KEY` to your Lambda environment variables.

### Phase 2: Frontend (Streamlit Community Cloud)

1. Fork or clone this repository.
2. Update the configuration variables at the top of `app.py`:
   ```python
   BUCKET_NAME   = "your-s3-bucket-name"
   QUEUE_URL     = "your-sqs-queue-url"
   REGION        = "your-aws-region"
