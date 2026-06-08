<div align="center">
  <h1>🚀 Pipeline Failure RCA Bot</h1>
  <p><b>An AI-powered Root Cause Analysis assistant for ETL and Cron pipeline failures.</b></p>

  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Flask](https://img.shields.io/badge/Flask-3.0.2-lightgrey.svg)](https://flask.palletsprojects.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
  [![Ollama](https://img.shields.io/badge/Ollama-Mistral-orange.svg)](https://ollama.com/)
  [![License](https://img.shields.io/badge/License-MIT-purple.svg)](#license)
</div>

---

## 📖 Overview

The **Pipeline Failure RCA Bot** is an intelligent, multi-agent Root Cause Analysis (RCA) application designed to automatically investigate pipeline failures. When an ETL or Cron job fails, identifying the root cause often requires manually sifting through thousands of log lines and correlating them with recent code changes. 

This bot automates the investigation by:
1. Parsing **failed execution logs** and comparing them with historical **successful runs**.
2. Auditing recent **GitHub commits and code diffs** to detect regressions.
3. Utilizing a local LLM (Mistral via **Ollama**) in a multi-agent reasoning loop to synthesize a complete incident report with a confidence score and actionable remediation steps.

---

## ✨ Key Features

- 🧠 **Multi-Agent AI Reasoning**: Utilizes dedicated AI agents for Log Analysis, GitHub Correlation, and RCA Generation.
- 🔄 **Code Regression Detection**: Connects to the GitHub REST API to pull recent commits and analyze code changes directly against the failing logs.
- 📊 **Historical Analysis**: Compares failure logs with the latest successful pipeline runs to spot behavioral anomalies.
- 📄 **PDF Export**: One-click generation of print-ready, professional RCA reports using `reportlab`.
- 💻 **Modern UI**: A beautiful, glassmorphism-styled dashboard built with Bootstrap 5 and Vanilla CSS.
- 🔒 **Privacy First**: Designed to run entirely locally using Ollama, keeping your sensitive pipeline logs and code diffs on your own infrastructure.

---

## 🏗️ System Architecture

```text
                       +-----------------------+
                       |   User Dashboard UI   |
                       +-----------+-----------+
                                   | (Upload Logs / Run Analyze)
                                   v
                       +-----------+-----------+
                       |     Flask Server      |
                       +-----+-----------+-----+
                             |           |
       +---------------------+           +---------------------+
       | Database (MongoDB)  |           |   GitHub REST API   |
       +----------+----------+           +----------+----------+
                  |                                 |
                  v                                 v
       +----------+---------------------------------+----------+
       |                   AI AGENT LOOP                       |
       |                                                       |
       |  +--------------------+       +--------------------+  |
       |  |  Agent 1: Log      |------>|  Agent 2: GitHub   |  |
       |  |  Analyzer          |       |  Analyzer          |  |
       |  +---------+----------+       +---------+----------+  |
       |            |                            |             |
       |            +------------+  +------------+             |
       |                         |  |                          |
       |                         v  v                          |
       |              +----------+----------+                  |
       |              |   Agent 3: RCA      |                  |
       |              |   Generator         |                  |
       |              +----------+----------+                  |
       +-------------------------|-----------------------------+
                                 v
                     +-----------+-----------+
                     |    RCA Report / PDF   |
                     +-----------------------+
```

---

## 🛠️ Technology Stack

- **Backend Framework**: Python, Flask
- **Database**: MongoDB (managed via `pymongo`)
- **AI / LLM Engine**: [Ollama](https://ollama.com) (Running the `mistral` model locally)
- **External APIs**: GitHub REST API
- **Frontend**: HTML5, Vanilla CSS, Bootstrap 5, Jinja2 Templates
- **Utilities**: `reportlab` for dynamic PDF generation, `python-dotenv` for configuration.

---

## 📂 Project Structure

```text
Pipeline_failure_RCA_Bot/
├── agents/             # Core logic for the AI Agents (Log, GitHub, RCA)
├── models/             # Database connection and schema definitions
├── routes/             # Flask Blueprints (upload, analysis, report)
├── services/           # DB wrapper and business logic layer
├── static/             # CSS styling, JS, and image assets
├── templates/          # Jinja2 HTML views (Dashboard, Reports)
├── logs/               # Application runtime logs
├── uploads/            # Temporary storage for uploaded pipeline logs
├── .env.example        # Example environment configuration
├── app.py              # Application entry point
├── config.py           # Configuration loader
└── requirements.txt    # Python dependencies
```

---

## ⚙️ Setup and Installation

### 1. Prerequisites
- **Python 3.8+**
- **MongoDB** (Local instance or remote cluster)
- **Ollama** installed on your host machine.

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/Pipeline_failure_RCA_Bot.git
cd Pipeline_failure_RCA_Bot
```

### 3. Install Python Dependencies
It is highly recommended to use a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Setup Local LLM with Ollama
Ensure Ollama is installed, running, and the Mistral model is pulled:
```bash
ollama pull mistral
```
*(Verify the Ollama service is accessible at `http://localhost:11434`)*

### 5. Environment Configuration
Create a `.env` file in the root directory:
```env
# MongoDB Connection URL
MONGODB_URI=mongodb://localhost:27017/rca_bot

# Ollama AI Configuration
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# GitHub API credentials (Required for Agent 2)
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=owner/repository

# Flask configs
SECRET_KEY=dev_secret_key_pipeline_rca_bot_12345
FLASK_ENV=development
PORT=5000
```

---

## 🚀 Usage

1. **Start the Application**:
   ```bash
   python app.py
   ```
2. **Access the Dashboard**:
   Open your web browser and navigate to `http://localhost:5000`.
3. **Upload Logs**:
   Upload a recent "Success" log as a baseline, followed by your failing pipeline log.
4. **Run Analysis**:
   Click "Analyze" to trigger the multi-agent AI loop. The system will ingest the logs, query the GitHub repository for recent commits, and synthesize a root cause.
5. **View & Export**:
   Review the detailed RCA report UI. If satisfied, export it to PDF for your team's post-mortem documentation.

---

## 📦 Database Collections

The application uses MongoDB to store execution history. It utilizes a `counters` collection to maintain auto-incrementing sequential IDs.
- **`logs`**: Stores uploaded pipeline text logs and their statuses.
- **`github_analysis`**: Caches correlated GitHub commit diff audits and file changes.
- **`reports`**: Stores synthesized AI root cause analyses, mapping them to specific logs and GitHub analyses.

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve the RCA accuracy, add support for more LLM providers (e.g., OpenAI, Anthropic), or enhance the UI:
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---
*Built with ❤️ for DevOps and Data Engineering teams.*
