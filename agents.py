"""
TireForge Multi-Agent System — Specialized Agents Module
Microsoft Azure AI Foundry SDK Implementation

Provides:
  - check_thresholds: Schema-validated python tool for telemetry validation
  - AnomalyDetectionAgent: Specialized agent for sensor threshold scanning
  - FaultDiagnosisAgent: Specialized agent for root-cause diagnosis & action planning
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from openai.types.responses.response_input_param import FunctionCallOutput


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


def check_thresholds(machine_id: str) -> str:
    """
    Reads sensor_data.json and checks if a machine's readings are within thresholds.
    Returns a JSON string detailing all readings and specific out-of-spec anomalies.
    """
    if not SENSOR_DATA_PATH.exists():
        return json.dumps({"error": f"Sensor data file not found at {SENSOR_DATA_PATH}"})

    with open(SENSOR_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    machine = None
    for m in data.get("machines", []):
        if m["machine_id"].upper() == machine_id.upper() or m["name"].lower() == machine_id.lower():
            machine = m
            break

    if not machine:
        return json.dumps({"error": f"Machine '{machine_id}' not found in telemetry database."})

    results = {
        "machine_id": machine["machine_id"],
        "name": machine["name"],
        "type": machine["type"],
        "status": machine["status"],
        "last_maintenance": machine.get("last_maintenance", "Unknown"),
        "anomalies": [],
        "all_readings": {},
    }

    for sensor, reading in machine["readings"].items():
        value = reading["value"]
        threshold = machine["thresholds"][sensor]
        in_spec = threshold["min"] <= value <= threshold["max"]

        results["all_readings"][sensor] = {
            "value": value,
            "unit": reading["unit"],
            "min": threshold["min"],
            "max": threshold["max"],
            "in_spec": in_spec,
        }

        if not in_spec:
            deviation = ""
            if value > threshold["max"]:
                pct = ((value - threshold["max"]) / threshold["max"]) * 100
                deviation = f"{pct:.1f}% above max ({threshold['max']}{reading['unit']})"
            elif value < threshold["min"]:
                pct = ((threshold["min"] - value) / threshold["min"]) * 100
                deviation = f"{pct:.1f}% below min ({threshold['min']}{reading['unit']})"

            results["anomalies"].append({
                "sensor": sensor,
                "value": value,
                "unit": reading["unit"],
                "threshold_min": threshold["min"],
                "threshold_max": threshold["max"],
                "deviation": deviation,
            })

    return json.dumps(results, indent=2)


CHECK_THRESHOLDS_TOOL = FunctionTool(
    name="check_thresholds",
    description="Check if a machine's sensor readings are within normal operating thresholds. Returns anomalies if any readings are out of spec.",
    parameters={
        "type": "object",
        "properties": {
            "machine_id": {
                "type": "string",
                "description": "The machine ID (e.g., 'MX-001', 'CP-003') or name (e.g., 'Mixer Alpha') to check",
            }
        },
        "required": ["machine_id"],
        "additionalProperties": False,
    },
    strict=False,
)


class AnomalyDetectionAgent:
    """Specialized Agent responsible for telemetry ingestion and threshold anomaly detection."""

    def __init__(self):
        self.agent = None
        self.client = None
        self.openai = None

    def create(self):
        if not PROJECT_CONNECTION_STRING:
            raise ValueError("PROJECT_CONNECTION_STRING missing from environment.")

        self.client = AIProjectClient(
            endpoint=PROJECT_CONNECTION_STRING,
            credential=DefaultAzureCredential(),
        )
        self.openai = self.client.get_openai_client()

        system_prompt = """
        You are an Industrial Telemetry & Anomaly Detection Agent for TireForge Industries.
        Your sole responsibility is to scan machine sensors, compare readings against nominal thresholds, and identify anomalies.

        Guidelines:
        1. When requested to inspect machines, use the check_thresholds tool for each machine ID.
        2. Format your response into a clear Markdown summary:
           - Machine Name & ID
           - Operational Status (NORMAL / WARNING / CRITICAL)
           - Out-of-spec Readings: Sensor name, current value, threshold, percentage deviation.
        3. Use 🟢 NORMAL, ⚠️ WARNING, and 🔴 CRITICAL badges.
        4. Be precise, conciseness is required. Ground all statements in tool responses.
        """

        self.agent = self.client.agents.create_version(
            agent_name="anomaly-detection-agent",
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT_NAME,
                instructions=system_prompt,
                tools=[CHECK_THRESHOLDS_TOOL],
            ),
        )
        return self.agent

    def run(self, input_text: str) -> str:
        conversation = self.openai.conversations.create()
        response = self.openai.responses.create(
            input=input_text,
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": self.agent.name, "type": "agent_reference"}},
        )

        while True:
            function_calls = [item for item in response.output if item.type == "function_call"]
            if not function_calls:
                break

            input_list = []
            for item in function_calls:
                if item.name == "check_thresholds":
                    args = json.loads(item.arguments)
                    result = check_thresholds(args.get("machine_id", ""))
                else:
                    result = json.dumps({"error": f"Unknown tool '{item.name}'"})

                input_list.append(
                    FunctionCallOutput(
                        type="function_call_output",
                        call_id=item.call_id,
                        output=result,
                    )
                )

            response = self.openai.responses.create(
                input=input_list,
                conversation=conversation.id,
                extra_body={"agent_reference": {"name": self.agent.name, "type": "agent_reference"}},
            )

        output_text = response.output_text
        self.openai.conversations.delete(conversation_id=conversation.id)
        return output_text

    def cleanup(self):
        if self.agent and self.client:
            self.client.agents.delete_version(
                agent_name=self.agent.name,
                agent_version=self.agent.version,
            )
            self.client.close()


class FaultDiagnosisAgent:
    """Specialized Agent responsible for physical fault reasoning and emergency action planning."""

    def __init__(self):
        self.agent = None
        self.client = None
        self.openai = None

    def create(self):
        if not PROJECT_CONNECTION_STRING:
            raise ValueError("PROJECT_CONNECTION_STRING missing from environment.")

        self.client = AIProjectClient(
            endpoint=PROJECT_CONNECTION_STRING,
            credential=DefaultAzureCredential(),
        )
        self.openai = self.client.get_openai_client()

        system_prompt = """
        You are a Mechanical Fault Diagnosis & Reliability Expert for TireForge Industries.
        Given sensor anomaly reports from factory machinery, perform root-cause reasoning and output actionable maintenance protocols.

        Diagnostic Matrix:
        - High Temperature + High Pressure -> Clog / Blockage / Thermal Overload
        - High Vibration Alone -> Mechanical Misalignment / Bearing Wear / Loose Mounting
        - High Temperature + High Vibration -> Lubrication Failure / Bearing Seizure Risk
        - Compound Critical Out-of-Spec -> Immediate System Failure Hazard

        Output Structure:
        LIKELY ROOT CAUSE: <detailed engineering diagnosis>
        MAINTENANCE ACTIONS: <step-by-step physical remediation steps>
        URGENCY LEVEL: IMMEDIATE (shutdown now) | WITHIN 24H | MONITOR
        REQUIRED SPARE PARTS: <suggested components>
        """

        self.agent = self.client.agents.create_version(
            agent_name="fault-diagnosis-agent",
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT_NAME,
                instructions=system_prompt,
            ),
        )
        return self.agent

    def run(self, input_text: str) -> str:
        conversation = self.openai.conversations.create()
        response = self.openai.responses.create(
            input=input_text,
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": self.agent.name, "type": "agent_reference"}},
        )
        output_text = response.output_text
        self.openai.conversations.delete(conversation_id=conversation.id)
        return output_text

    def cleanup(self):
        if self.agent and self.client:
            self.client.agents.delete_version(
                agent_name=self.agent.name,
                agent_version=self.agent.version,
            )
            self.client.close()


if __name__ == "__main__":
    print("Testing check_thresholds locally...")
    print(check_thresholds("MX-001"))
    print("\ncheck_thresholds test completed successfully!")
