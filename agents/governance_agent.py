import os
import yaml
import json
import hashlib
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from copy import deepcopy

load_dotenv()

# Configuration
GROQ_API_KEY    = os.getenv('GROQ_API_KEY')
METRICS_PATH    = os.getenv('METRICS_PATH', './metrics')
GOVERNANCE_PATH = os.getenv('GOVERNANCE_PATH', './governance')
REPORTS_PATH    = os.getenv('REPORTS_PATH', './reports')

# ─────────────────────────────────────────────
# REC 5 — CONFIDENCE-BASED HUMAN TRIAGE
# Change proposals where AI confidence < threshold are routed to
# a triage queue for human review instead of being auto-processed.
# Override via .env:  CONFIDENCE_THRESHOLD=90
# ─────────────────────────────────────────────
CONFIDENCE_THRESHOLD = int(os.getenv('CONFIDENCE_THRESHOLD', '90'))
TRIAGE_QUEUE_FILE    = os.path.join(os.getenv('GOVERNANCE_PATH', './governance'),
                                    'triage_queue.yaml')

client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────
# 1. LOAD METRIC FILE
# ─────────────────────────────────────────────
def load_metric_file(table_name):
    """Load metric YAML file for a table."""
    filepath = os.path.join(METRICS_PATH, f'{table_name}_metrics.yaml')
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def save_metric_file(table_name, data):
    """Save updated metric YAML file."""
    filepath = os.path.join(METRICS_PATH, f'{table_name}_metrics.yaml')
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

# ─────────────────────────────────────────────
# 2. VERSION CONTROL
# ─────────────────────────────────────────────
def get_metric_hash(metric):
    metric_str = json.dumps(metric, sort_keys=True)
    return hashlib.md5(metric_str.encode()).hexdigest()[:8]

def load_version_history(table_name):
    os.makedirs(GOVERNANCE_PATH, exist_ok=True)
    history_file = os.path.join(GOVERNANCE_PATH, f'{table_name}_history.yaml')
    if not os.path.exists(history_file):
        return []
    with open(history_file, 'r') as f:
        return yaml.safe_load(f) or []

def save_version_history(table_name, history):
    os.makedirs(GOVERNANCE_PATH, exist_ok=True)
    history_file = os.path.join(GOVERNANCE_PATH, f'{table_name}_history.yaml')
    with open(history_file, 'w') as f:
        yaml.dump(history, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def create_version_snapshot(table_name, metrics, change_type, changed_by, change_reason):
    history     = load_version_history(table_name)
    version_num = len(history) + 1
    snapshot = {
        'version':       version_num,
        'timestamp':     datetime.now().isoformat(),
        'changed_by':    changed_by,
        'change_type':   change_type,
        'change_reason': change_reason,
        'metrics_hash':  get_metric_hash(metrics),
        'metrics':       deepcopy(metrics)
    }
    history.append(snapshot)
    save_version_history(table_name, history)
    print(f"  Version {version_num} snapshot created for '{table_name}'")
    return version_num

# ─────────────────────────────────────────────
# 3. AUDIT LOG
# ─────────────────────────────────────────────
def load_audit_log():
    os.makedirs(GOVERNANCE_PATH, exist_ok=True)
    audit_file = os.path.join(GOVERNANCE_PATH, 'audit_log.yaml')
    if not os.path.exists(audit_file):
        return []
    with open(audit_file, 'r') as f:
        return yaml.safe_load(f) or []

def append_audit_log(entry):
    audit_log  = load_audit_log()
    audit_log.append(entry)
    audit_file = os.path.join(GOVERNANCE_PATH, 'audit_log.yaml')
    with open(audit_file, 'w') as f:
        yaml.dump(audit_log, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def log_change(table_name, metric_name, change_type, old_value, new_value,
               changed_by, reason, status):
    entry = {
        'timestamp':   datetime.now().isoformat(),
        'table':       table_name,
        'metric_name': metric_name,
        'change_type': change_type,
        'old_value':   old_value,
        'new_value':   new_value,
        'changed_by':  changed_by,
        'reason':      reason,
        'status':      status
    }
    append_audit_log(entry)
    return entry

# ─────────────────────────────────────────────
# REC 5 — ESCALATE TO HUMAN TRIAGE
# ─────────────────────────────────────────────
def escalate_to_human(table_name, metric_name, change_type,
                      old_metric, new_metric, reason,
                      changed_by, validation):
    """
    Write a low-confidence proposal to the triage queue for human review.
    Called when AI confidence < CONFIDENCE_THRESHOLD.
    """
    os.makedirs(GOVERNANCE_PATH, exist_ok=True)
    queue = []
    if os.path.exists(TRIAGE_QUEUE_FILE):
        with open(TRIAGE_QUEUE_FILE, 'r') as f:
            queue = yaml.safe_load(f) or []

    triage_entry = {
        'queued_at':    datetime.now().isoformat(),
        'table':        table_name,
        'metric_name':  metric_name,
        'change_type':  change_type,
        'old_metric':   old_metric,
        'new_metric':   new_metric,
        'reason':       reason,
        'changed_by':   changed_by,
        'ai_confidence':  validation.get('confidence', 0),
        'ai_assessment':  validation.get('assessment', ''),
        'ai_concerns':    validation.get('concerns', []),
        'status':       'PENDING_HUMAN_REVIEW',
    }
    queue.append(triage_entry)

    with open(TRIAGE_QUEUE_FILE, 'w') as f:
        yaml.dump(queue, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\n  [TRIAGE] Confidence {validation.get('confidence')}% < "
          f"threshold {CONFIDENCE_THRESHOLD}%")
    print(f"  [TRIAGE] Proposal queued for human review -> {TRIAGE_QUEUE_FILE}")

    # Also log to audit trail with TRIAGE status
    log_change(table_name, metric_name, change_type,
               old_metric, new_metric, changed_by, reason, 'TRIAGE')

# ─────────────────────────────────────────────
# 4. AI VALIDATION
# ─────────────────────────────────────────────
def ai_validate_change(table_name, metric_name, change_type,
                       old_metric, new_metric, reason):
    prompt = f"""
You are a data governance officer reviewing a proposed change to a business metric.

Table        : {table_name}
Metric       : {metric_name}
Change Type  : {change_type}
Reason Given : {reason}

BEFORE:
{json.dumps(old_metric, indent=2)}

AFTER:
{json.dumps(new_metric, indent=2)}

Evaluate this change and return ONLY a valid JSON object:
{{
  "approved": true or false,
  "confidence": 0-100,
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "assessment": "One sentence assessment",
  "concerns": ["concern1", "concern2"],
  "recommendations": ["recommendation1"]
}}

Approve if: the change is logically sound, reason is valid, no major business impact.
Reject if: aggregation type change breaks business logic, or no valid reason given.
"""

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = response.choices[0].message.content.strip()

    if response_text.startswith('```'):
        parts = response_text.split('```')
        response_text = parts[1]
        if response_text.lower().startswith('json'):
            response_text = response_text[4:]

    return json.loads(response_text.strip())

# ─────────────────────────────────────────────
# 5. PROPOSE METRIC CHANGE  (Rec 5: confidence triage added)
# ─────────────────────────────────────────────
def propose_change(table_name, metric_name, field_to_change,
                   new_value, changed_by, reason):
    """Propose a change to a metric — runs AI validation and approval workflow."""
    print(f"\n{'─'*50}")
    print(f"  CHANGE PROPOSAL")
    print(f"  Table   : {table_name}")
    print(f"  Metric  : {metric_name}")
    print(f"  Change  : {field_to_change} -> '{new_value}'")
    print(f"  By      : {changed_by}")
    print(f"  Reason  : {reason}")

    data = load_metric_file(table_name)
    if not data:
        print(f"  ERROR: Metric file not found for '{table_name}'")
        return None

    metrics = data.get('metrics', [])
    metric  = next((m for m in metrics if m['metric_name'] == metric_name), None)
    if not metric:
        print(f"  ERROR: Metric '{metric_name}' not found in '{table_name}'")
        return None

    old_metric = deepcopy(metric)
    new_metric = deepcopy(metric)
    new_metric[field_to_change] = new_value

    print(f"\n  Running AI validation...")
    validation = ai_validate_change(
        table_name, metric_name,
        f"UPDATE_{field_to_change.upper()}",
        old_metric, new_metric, reason
    )

    approved   = validation.get('approved', False)
    risk_level = validation.get('risk_level', 'UNKNOWN')
    confidence = validation.get('confidence', 0)

    print(f"  AI Decision   : {'APPROVED' if approved else 'REJECTED'}")
    print(f"  Risk Level    : {risk_level}")
    print(f"  Confidence    : {confidence}%")
    print(f"  Assessment    : {validation.get('assessment', '')}")

    if validation.get('concerns'):
        print(f"  Concerns:")
        for c in validation['concerns']:
            print(f"    * {c}")

    if validation.get('recommendations'):
        print(f"  Recommendations:")
        for r in validation['recommendations']:
            print(f"    -> {r}")

    # ── Rec 5: route low-confidence proposals to triage ──────────
    if confidence < CONFIDENCE_THRESHOLD:
        escalate_to_human(
            table_name, metric_name,
            f"UPDATE_{field_to_change.upper()}",
            old_metric, new_metric, reason, changed_by, validation
        )
        return {
            'status':     'TRIAGE',
            'validation': validation,
            'old_metric': old_metric,
            'new_metric': new_metric
        }

    status = 'APPROVED' if approved else 'REJECTED'

    if approved:
        create_version_snapshot(
            table_name, metrics,
            f"PRE_CHANGE_{field_to_change.upper()}",
            changed_by, reason
        )
        metric[field_to_change]  = new_value
        data['metrics']          = metrics
        data['last_modified']    = datetime.now().isoformat()
        save_metric_file(table_name, data)
        print(f"\n  Change applied to {table_name}_metrics.yaml")
        create_version_snapshot(
            table_name, metrics,
            f"POST_CHANGE_{field_to_change.upper()}",
            changed_by, reason
        )
    else:
        print(f"\n  Change rejected -- metric file unchanged.")

    log_change(
        table_name, metric_name,
        f"UPDATE_{field_to_change.upper()}",
        {field_to_change: old_metric.get(field_to_change)},
        {field_to_change: new_value},
        changed_by, reason, status
    )
    print(f"  Audit log updated.")

    return {
        'status':     status,
        'validation': validation,
        'old_metric': old_metric,
        'new_metric': new_metric if approved else old_metric
    }

# ─────────────────────────────────────────────
# 6. ADD NEW METRIC  (Rec 5: confidence triage added)
# ─────────────────────────────────────────────
def add_metric(table_name, new_metric, changed_by, reason):
    """Propose adding a new metric to a table."""
    print(f"\n{'─'*50}")
    print(f"  ADD METRIC PROPOSAL")
    print(f"  Table   : {table_name}")
    print(f"  Metric  : {new_metric.get('metric_name')}")
    print(f"  By      : {changed_by}")

    data = load_metric_file(table_name)
    if not data:
        print(f"  ERROR: Metric file not found for '{table_name}'")
        return None

    metrics  = data.get('metrics', [])
    existing = next((m for m in metrics
                     if m['metric_name'] == new_metric['metric_name']), None)
    if existing:
        print(f"  WARNING: Metric '{new_metric['metric_name']}' already exists!")
        return None

    print(f"  Running AI validation...")
    validation = ai_validate_change(
        table_name, new_metric['metric_name'],
        'ADD_METRIC', {}, new_metric, reason
    )

    approved   = validation.get('approved', False)
    confidence = validation.get('confidence', 0)
    print(f"  AI Decision: {'APPROVED' if approved else 'REJECTED'}")
    print(f"  Confidence : {confidence}%")
    print(f"  Assessment : {validation.get('assessment', '')}")

    # ── Rec 5: triage low-confidence additions ────────────────────
    if confidence < CONFIDENCE_THRESHOLD:
        escalate_to_human(
            table_name, new_metric['metric_name'],
            'ADD_METRIC', {}, new_metric, reason, changed_by, validation
        )
        return {'status': 'TRIAGE', 'validation': validation}

    if approved:
        create_version_snapshot(table_name, metrics, 'PRE_ADD_METRIC',
                                changed_by, reason)
        metrics.append(new_metric)
        data['metrics']       = metrics
        data['last_modified'] = datetime.now().isoformat()
        save_metric_file(table_name, data)
        create_version_snapshot(table_name, metrics, 'POST_ADD_METRIC',
                                changed_by, reason)
        print(f"  New metric added.")

    log_change(table_name, new_metric['metric_name'], 'ADD_METRIC',
               {}, new_metric, changed_by, reason,
               'APPROVED' if approved else 'REJECTED')

    return {'status': 'APPROVED' if approved else 'REJECTED', 'validation': validation}

# ─────────────────────────────────────────────
# 7. GOVERNANCE SUMMARY  (Rec 5: triage queue count added)
# ─────────────────────────────────────────────
def governance_summary():
    """Print a summary of all governance activity including triage queue."""
    audit_log = load_audit_log()

    approved = [e for e in audit_log if e.get('status') == 'APPROVED']
    rejected = [e for e in audit_log if e.get('status') == 'REJECTED']
    triage   = [e for e in audit_log if e.get('status') == 'TRIAGE']

    print("\n" + "="*60)
    print("  GOVERNANCE SUMMARY")
    print("="*60)
    print(f"  Total changes logged : {len(audit_log)}")
    print(f"  Approved             : {len(approved)}")
    print(f"  Rejected             : {len(rejected)}")
    print(f"  Triage (human review): {len(triage)}")

    if triage:
        print(f"\n  Pending Triage Items (confidence < {CONFIDENCE_THRESHOLD}%):")
        for e in triage:
            print(f"    [TRIAGE] [{e['timestamp'][:19]}] "
                  f"{e['table']}.{e['metric_name']} by {e['changed_by']}")
        print(f"  Full triage queue -> {TRIAGE_QUEUE_FILE}")

    if audit_log:
        print(f"\n  Recent Activity:")
        for entry in audit_log[-5:]:
            status = entry.get('status', '?')
            icon   = {'APPROVED': '[OK]', 'REJECTED': '[NO]',
                      'TRIAGE':   '[!!]'}.get(status, '[?]')
            print(f"  {icon} [{entry['timestamp'][:19]}] "
                  f"{entry['table']}.{entry['metric_name']} "
                  f"-- {entry['change_type']} by {entry['changed_by']}")

    print("="*60)

# ─────────────────────────────────────────────
# ENTRY POINT -- Demo Scenarios
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  GOVERNANCE AGENT -- Starting")
    print(f"  Confidence threshold : {CONFIDENCE_THRESHOLD}%")
    print("="*60)

    # Scenario 1: Valid change -- fix type mismatch
    print("\nScenario 1: Fix type mismatch -- 'return_rate' in store_returns")
    propose_change(
        table_name      = 'store_returns',
        metric_name     = 'return_rate',
        field_to_change = 'type',
        new_value       = 'avg',
        changed_by      = 'selvi.durai@ljmu.ac.uk',
        reason          = 'Standardising return_rate to AVG across all return tables for consistency'
    )

    # Scenario 2: Valid change -- update description
    print("\nScenario 2: Update metric description -- 'total_net_profit' in store_sales")
    propose_change(
        table_name      = 'store_sales',
        metric_name     = 'total_net_profit',
        field_to_change = 'description',
        new_value       = 'Sum of net profit after deducting wholesale cost and discounts from sales revenue',
        changed_by      = 'selvi.durai@ljmu.ac.uk',
        reason          = 'Improving metric description clarity for business users'
    )

    # Scenario 3: Risky change -- should be rejected
    print("\nScenario 3: Risky change -- altering aggregation type without valid reason")
    propose_change(
        table_name      = 'store_sales',
        metric_name     = 'total_sales',
        field_to_change = 'type',
        new_value       = 'count',
        changed_by      = 'unknown_user',
        reason          = 'Just trying something'
    )

    # Scenario 4: Add new metric
    print("\nScenario 4: Add new metric -- 'gross_margin' to catalog_sales")
    add_metric(
        table_name = 'catalog_sales',
        new_metric = {
            'metric_name':    'gross_margin',
            'display_name':   'Gross Margin',
            'description':    'Difference between total sales and wholesale cost',
            'column':         'cs_net_profit',
            'type':           'sum',
            'category':       'finance',
            'business_rules': 'Calculated as net_paid minus wholesale_cost'
        },
        changed_by = 'selvi.durai@ljmu.ac.uk',
        reason     = 'Adding gross margin metric for profitability analysis in thesis'
    )

    governance_summary()
