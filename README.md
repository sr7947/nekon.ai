# 🏭 TireForge Industrial Multi-Agent System
### Microsoft Agent-A-Thon & Founderz AI Business School Final Submission

This codebase delivers a production-ready, multi-agent AI solution built with **Microsoft Azure AI Foundry SDK** (`azure-ai-projects`, `azure-identity`, OpenTelemetry, Promptflow Evals) for automated industrial anomaly detection, fault diagnosis, and maintenance orchestration.

---

## 📁 Repository Structure

```
├── agents.py             # Specialized AnomalyDetectionAgent & FaultDiagnosisAgent definitions + check_thresholds tool
├── monitor.py            # OpenTelemetry & Application Insights GenAI tracing setup
├── evaluate.py           # Offline evaluation pipeline with LLM-as-Judge scoring against golden dataset
├── deploy.py             # End-to-end multi-agent orchestration & Foundry WorkflowAgentDefinition registration
├── sensor_data.json      # Real-time multi-sensor telemetry dataset (temperature, vibration, pressure, RPM)
├── eval_portal.jsonl     # 10-scenario golden evaluation dataset for Microsoft Foundry portal / offline evals
├── requirements.txt      # Python dependencies (azure-ai-projects, opentelemetry, promptflow-evals)
├── .env.example          # Environment variables configuration template
└── README.md             # Technical documentation & execution guide
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup
Create a virtual environment and install dependencies:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

Copy the `.env.example` file to `.env` and fill in your Azure AI Foundry details:
```bash
cp .env.example .env
```

---

### 2. Run Python Multi-Agent Pipeline (`agents.py` & `deploy.py`)
To execute the multi-agent pipeline:
```bash
python deploy.py
```
**Output Highlights**:
- Ingests telemetry for 5 critical machines (`MX-001`, `EX-002`, `CP-003`, `CU-004`, `IS-005`).
- Executes `AnomalyDetectionAgent` with tool calls (`check_thresholds`).
- Passes identified anomalies to `FaultDiagnosisAgent` for root-cause analysis and action planning.
- Prints consolidated **TireForge Factory Health Report**.
- Outputs Microsoft Foundry Portal `WorkflowAgentDefinition` (YAML).

---

### 3. Enable Observability & Tracing (`monitor.py`)
To configure OpenTelemetry instrumentation and verify telemetry span generation:
```bash
python monitor.py
```
Configures `AIProjectInstrumentor` and connects to Azure Application Insights to capture latency, token consumption, tool executions, and step-by-step agent spans.

---

### 4. Run Quality Evaluations (`evaluate.py`)
To run systematic offline evaluations against the 10-scenario golden dataset:
```bash
python evaluate.py
```
Evaluates output quality across **Coherence**, **Fluency**, **Groundedness**, and **Task Adherence** (Pass/Fail).

---

## 🏆 Assessment Submission Artifacts

- **Submission Document**: Comprehensive 3-Step Solution Design, Production-Readiness Plan, and End-to-End Architecture Document (formatted for PDF/Word export).
- **Presentation Script**: Timed video presentation transcript with slide-by-slide visuals and narration text.
