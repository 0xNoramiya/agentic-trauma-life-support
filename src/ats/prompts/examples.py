"""One-shot in-context example for the Drafter.

A single tension-pneumothorax case used as a demonstrator for the model.
The JSON validates against `TriageOutput` and is intentionally compact.
"""

from __future__ import annotations

EXAMPLE_VIGNETTE_EN = (
    "30M motorbike vs car, ejected. RR 32, SpO2 88% on room air, HR 124, BP 92/60, GCS 14. "
    "Decreased breath sounds on the left, tracheal deviation to the right."
)


EXAMPLE_OUTPUT_JSON = """{
  "case_id": "example_tension_ptx",
  "patient_brief": {
    "age": 30,
    "sex": "M",
    "mechanism": "motorbike vs car, ejected"
  },
  "primary_survey": {
    "A_airway": {
      "concern_level": "high",
      "imaging_findings": [
        {
          "finding": "tracheal deviation to the right",
          "laterality": "right",
          "severity": "moderate",
          "citation_id": "atls-c1-001"
        }
      ],
      "actions_required": [
        "maintain manual airway, prepare for definitive airway after decompression"
      ]
    },
    "B_breathing": {
      "concern_level": "critical",
      "rr": 32,
      "spo2": 88,
      "imaging_findings": [
        {
          "finding": "left tension pneumothorax",
          "laterality": "left",
          "severity": "severe",
          "citation_id": "east-ptx-002"
        }
      ],
      "actions_required": [
        "immediate needle decompression at left 5th ICS, mid-axillary line",
        "place left-sided 28F chest tube"
      ]
    },
    "C_circulation": {
      "concern_level": "high",
      "hr": 124,
      "sbp": 92,
      "dbp": 60,
      "imaging_findings": [],
      "actions_required": [
        "two large-bore IVs",
        "1L warmed crystalloid bolus, then reassess",
        "send type and screen, lactate"
      ]
    },
    "D_disability": {
      "concern_level": "moderate",
      "gcs": 14,
      "actions_required": [
        "serial GCS, finger-stick glucose"
      ]
    },
    "E_exposure": {
      "concern_level": "moderate",
      "temp": 36.4,
      "actions_required": [
        "fully expose, log-roll, warm blankets"
      ]
    }
  },
  "disposition": {
    "priority": "immediate",
    "recommended_actions": [
      {
        "action": "needle decompression of left chest at 5th ICS, mid-axillary line",
        "rationale": "tension physiology with hypoxia and tracheal deviation",
        "urgency": "now",
        "citation_id": "east-ptx-002"
      },
      {
        "action": "trauma surgery to bedside",
        "rationale": "operative chest pathology likely",
        "urgency": "<5min",
        "citation_id": "atls-c1-001"
      }
    ],
    "escalation": {"who": "trauma surgery attending", "when": "now"},
    "additional_imaging": ["CT chest after decompression"],
    "labs": ["type and screen", "lactate", "ABG"]
  },
  "red_flags": [
    {
      "flag": "tension pneumothorax physiology",
      "evidence": ["SpO2 88%", "HR 124", "BP 92/60", "tracheal deviation right"],
      "immediate_action": "needle decompression of left chest now"
    }
  ],
  "citations": [
    {
      "id": "atls-c1-001",
      "source": "ACS ATLS",
      "section": "Chapter 1 — Initial Assessment",
      "quote": "Treat tension pneumothorax with immediate needle decompression before chest radiography.",
      "url": null
    },
    {
      "id": "east-ptx-002",
      "source": "EAST PMG",
      "section": "Pneumothorax",
      "quote": "Tube thoracostomy is recommended after decompression for confirmed pneumothorax in the trauma patient.",
      "url": null
    }
  ],
  "model_metadata": {
    "model": "Qwen/Qwen2.5-VL-72B-Instruct",
    "confidence": "moderate",
    "limitations": ["single AP portable view, no lateral", "image quality limits subtle findings"],
    "disclaimer": "Decision support only. Not a diagnosis. Not for unsupervised clinical use.",
    "verifier_notes": []
  }
}"""
