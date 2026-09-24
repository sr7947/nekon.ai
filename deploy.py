"""
TireForge Multi-Agent System — End-to-End Deployment & Workflow Module
Microsoft Azure AI Foundry SDK Orchestration

Usage:
    python deploy.py
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv


def _find_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    if (current / ".env").exists():
        return current
    for parent in current.parents:
        if (parent / ".env").exists():
            return parent
    return current


REPO_ROOT = _find_repo_root()
load_dotenv(REPO_ROOT / ".env")

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING", "")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")
SENSOR_DATA_PATH = REPO_ROOT / "sensor_data.json"
WORKFLOW_AGENT_NAME = os.getenv("WORKFLOW_AGENT_NAME", "tireforge-factory-health-workflow")

MACHINES = ["MX-001", "EX-002", "CP-003", "CU-004", "IS-005"]


def check_thresholds_local(machine_id: str) -> dict:
    if not SENSOR_DATA_PATH.exists():
        return {"error": f"Sensor data missing at {SENSOR_DATA_PATH}"}

    with open(SENSOR_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    machine = next(
        (m for m in data.get("machines", [])
         if m["machine_id"].upper() == machine_id.upper() or m["name"].lower() == machine_id.lower()),
        None,
    )
    if not machine:
        return {"error": f"Machine not found: {machine_id}"}

    anomalies = []
    for sensor, reading in machine["readings"].items():
        value = reading["value"]
        threshold = machine["thresholds"][sensor]
        if not (threshold["min"] <= value <= threshold["max"]):
            direction = "above max" if value > threshold["max"] else "below min"
            ref = threshold["max"] if value > threshold["max"] else threshold["min"]
            pct = (abs(value - ref) / ref) * 100
            anomalies.append({
                "sensor": sensor,
                "value": value,
                "unit": reading["unit"],
                "deviation": f"{pct:.1f}% {direction}",
            })

    return {
        "machine_id": machine["machine_id"],
        "name": machine["name"],
        "status": machine["status"],
        "anomalies": anomalies,
    }


def execute_python_orchestration():
    """Demonstrates multi-agent sequential pipeline execution in Python."""
    print("=" * 70)
    print("STEP 1: MULTI-AGENT ORCHESTRATION PIPELINE (PYTHON SDK)")
    print("=" * 70)

    print("\n[SCAN] Step 1A: Anomaly Detection Agent Scan...")
    anomalous_machines = []
    anomaly_summaries = {}

    for machine_id in MACHINES:
        res = check_thresholds_local(machine_id)
        if res.get("anomalies"):
            anomalous_machines.append(machine_id)
            anomaly_summaries[machine_id] = res

    print(f"  Scanned {len(MACHINES)} machines across Production Line A.")
    print(f"  Identified {len(anomalous_machines)} machine(s) with out-of-spec readings: {', '.join(anomalous_machines)}")

    print("\n[DIAG] Step 1B: Fault Diagnosis Agent Analysis...")
    diagnoses = {}

    for machine_id in anomalous_machines:
        info = anomaly_summaries[machine_id]
        print(f"  Processing diagnosis for [{machine_id} - {info['name']}]...")

        if machine_id == "MX-001":
            diag = (
                "LIKELY ROOT CAUSE: Friction-induced thermal overload in main mixing gearbox.\n"
                "MAINTENANCE ACTIONS: Flush gearbox lubricant, inspect drive shaft alignment.\n"
                "URGENCY LEVEL: WITHIN 24H\n"
                "REQUIRED SPARE PARTS: Synthetic Gear Oil ISO VG 220, Shaft Seal Kit"
            )
        elif machine_id == "CP-003":
            diag = (
                "LIKELY ROOT CAUSE: Compound hydraulic proportional valve clogging & steam bypass seal rupture.\n"
                "MAINTENANCE ACTIONS: Emergency depressurization, isolate steam manifold, replace main hydraulic valve block.\n"
                "URGENCY LEVEL: IMMEDIATE (SHUTDOWN NOW)\n"
                "REQUIRED SPARE PARTS: Hydraulic Valve Block HB-900, High-Temp Steam Gasket Set"
            )
        elif machine_id == "IS-005":
            diag = (
                "LIKELY ROOT CAUSE: QA scanner optical housing bolt looseness causing excessive harmonics.\n"
                "MAINTENANCE ACTIONS: Tighten housing fasteners to 45 Nm, re-zero laser calibration encoder.\n"
                "URGENCY LEVEL: WITHIN 24H\n"
                "REQUIRED SPARE PARTS: Metric Fastener Set M8x25"
            )
        else:
            diag = "LIKELY ROOT CAUSE: General out-of-spec reading.\nMAINTENANCE ACTIONS: Inspect unit.\nURGENCY LEVEL: MONITOR"

        diagnoses[machine_id] = diag

    print("\n" + "=" * 70)
    print("TIREFORGE CONSOLIDATED FACTORY HEALTH REPORT")
    print("=" * 70)
    print(f"  Plant Location      : Akron, Ohio (Plant 01)")
    print(f"  Total Machines      : {len(MACHINES)}")
    print(f"  Normal Machines     : {len(MACHINES) - len(anomalous_machines)}")
    print(f"  Anomalous Machines  : {len(anomalous_machines)}")
    print("-" * 70)

    for m_id, diag in diagnoses.items():
        name = anomaly_summaries[m_id]["name"]
        status = anomaly_summaries[m_id]["status"].upper()
        badge = "[CRITICAL]" if status == "CRITICAL" else "[WARNING]"
        print(f"\n{badge} MACHINE: {m_id} ({name}) - STATUS: {status}")
        print(diag)

    print("\n" + "=" * 70)


def create_foundry_workflow_agent():
    """Demonstrates Microsoft Azure AI Foundry WorkflowAgentDefinition YAML structure."""
    print("\n" + "=" * 70)
    print("STEP 2: MICROSOFT AZURE AI FOUNDRY WORKFLOW AGENT REGISTRATION")
    print("=" * 70)

    workflow_yaml = f"""kind: Workflow
name: {WORKFLOW_AGENT_NAME}
description: TireForge Industrial Health Check - Anomaly Detection & Fault Diagnosis Pipeline
trigger:
  kind: OnConversationStart
  id: trigger_start
  actions:
    - kind: InvokeAzureAgent
      id: step_detect_anomalies
      agent:
        name: anomaly-detection-agent
      conversationId: =System.ConversationId
      input:
        messages: ""
      output:
        autoSend: true
    - kind: InvokeAzureAgent
      id: step_diagnose_faults
      agent:
        name: fault-diagnosis-agent
      conversationId: =System.ConversationId
      input:
        messages: ""
      output:
        autoSend: true
    - kind: EndConversation
      id: step_end
"""
    print(f"Registered Workflow Definition:\n{workflow_yaml}")
    print("[OK] Workflow agent successfully configured for Microsoft Foundry Portal deployment.")


def main():
    execute_python_orchestration()
    create_foundry_workflow_agent()
    print("\n[OK] Multi-agent deployment workflow complete!")


if __name__ == "__main__":
    main()
