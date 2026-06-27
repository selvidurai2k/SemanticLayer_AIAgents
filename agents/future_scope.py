"""
future_scope.py
===============
Planned enhancements — NOT YET IMPLEMENTED
-------------------------------------------
This file contains two future recommendations that were evaluated
but deferred from the current implementation:

  Rec 2 — Portable Interchange Format (OSI-style)
  ─────────────────────────────────────────────────
  Export generated metrics in a vendor-neutral YAML/JSON structure
  so they can be consumed by tools other than Cube.js (e.g. dbt
  Semantic Layer, Looker LookML, Apache Superset).  A draft mapping
  is included below (see _build_portable_metric).

  NOTE: OSI v0.1 (Open Semantic Interchange) is an emerging proposal,
  not yet a ratified standard. This feature should be implemented once
  a stable community specification exists.

  Rec 4 — Continuous Change and Query Log Monitors
  ──────────────────────────────────────────────────
  Shift the framework from a batch execution model to a continuous,
  event-driven monitoring service.

  Two monitors are planned:
    SchemaChangeMonitor — watches PostgreSQL for DDL events
                          (column added/renamed/dropped) and triggers
                          automatic metric re-evaluation.
    QueryLogMonitor     — watches pg_stat_statements for ungoverned
                          aggregation patterns and auto-drafts new
                          metric proposals through the governance
                          workflow (including confidence triage).

STATUS : NOT YET IMPLEMENTED
DEPENDS: metric_definition_agent.py, governance_agent.py, governed_metric_api.py
"""

import os
import time
import json
import yaml
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── shared config (mirrors metric_definition_agent.py) ────────────
DB_HOST         = os.getenv('DB_HOST', 'localhost')
DB_PORT         = os.getenv('DB_PORT', '5432')
DB_NAME         = os.getenv('DB_NAME', 'tpcds')
DB_USER         = os.getenv('DB_USER', 'cube')
DB_PASS         = os.getenv('DB_PASS', 'cube_pass')
METRICS_PATH    = os.getenv('METRICS_PATH', './metrics')
GOVERNANCE_PATH = os.getenv('GOVERNANCE_PATH', './governance')

SCHEMA_POLL_INTERVAL = int(os.getenv('SCHEMA_POLL_INTERVAL', '300'))   # seconds
QUERY_POLL_INTERVAL  = int(os.getenv('QUERY_POLL_INTERVAL',  '600'))   # seconds


# ═══════════════════════════════════════════════════════════════════
# REC 2 — Portable Metric Interchange Format
# ═══════════════════════════════════════════════════════════════════
# Aggregation mapping: internal token → portable standard token
_PORTABLE_AGG_MAP = {
    'sum':   'SUM',
    'avg':   'AVERAGE',
    'count': 'COUNT',
    'min':   'MIN',
    'max':   'MAX',
}

# Category mapping: internal → semantic type
_PORTABLE_TYPE_MAP = {
    'finance':   'FINANCIAL',
    'sales':     'REVENUE',
    'returns':   'OPERATIONAL',
    'inventory': 'OPERATIONAL',
    'customer':  'CUSTOMER',
}


def _build_portable_metric(m):
    """Convert an internal metric dict to a vendor-neutral interchange structure."""
    return {
        'name':                 m['metric_name'],
        'label':                m['display_name'],
        'description':          m['description'],
        'source_column':        m['column'],
        'aggregation_function': _PORTABLE_AGG_MAP.get(m.get('type', '').lower(), 'SUM'),
        'semantic_type':        _PORTABLE_TYPE_MAP.get(m.get('category', '').lower(), 'OPERATIONAL'),
        'business_rules':       m.get('business_rules', 'None'),
    }


def save_metrics_portable(table_name, metrics, metrics_path='./metrics'):
    """
    Export metrics in a vendor-neutral YAML format that can be
    consumed by tools other than Cube.js (dbt, Looker, Superset).

    To activate: call this function after save_metrics_to_yaml()
    in metric_definition_agent.run_agent() once a target interchange
    specification has been agreed on with the consuming tool.

    Output file: <metrics_path>/<table_name>_metrics_portable.yaml
    """
    import yaml, os
    from datetime import datetime

    os.makedirs(metrics_path, exist_ok=True)
    doc = {
        'format_version': '0.1-draft',
        'source_table':   table_name,
        'generated_at':   datetime.now().isoformat(),
        'generated_by':   'MetricDefinitionAgent v1.0',
        'metrics':        [_build_portable_metric(m) for m in metrics],
    }
    out = os.path.join(metrics_path, f'{table_name}_metrics_portable.yaml')
    with open(out, 'w') as f:
        yaml.dump(doc, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"  [Portable] -> {out}")
    return out


# ───────────────────────────────────────────────────────────────────


def _get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=int(DB_PORT),
        dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )


def _write_drift_report(table_name, old_cols, new_cols):
    """Append a schema-drift event to governance/drift_report.yaml."""
    os.makedirs(GOVERNANCE_PATH, exist_ok=True)
    report_file = os.path.join(GOVERNANCE_PATH, 'drift_report.yaml')
    report = []
    if os.path.exists(report_file):
        with open(report_file, 'r') as f:
            report = yaml.safe_load(f) or []
    report.append({
        'timestamp':  datetime.now().isoformat(),
        'table':      table_name,
        'old_columns': old_cols,
        'new_columns': new_cols,
        'status':     'STALE — re-evaluation triggered',
    })
    with open(report_file, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    print(f"[SchemaMonitor] Drift report updated -> {report_file}")


# ═══════════════════════════════════════════════════════════════════
# MONITOR 1 — Schema Change Monitor
# ═══════════════════════════════════════════════════════════════════
def watch_schema_changes(poll_interval_seconds=SCHEMA_POLL_INTERVAL):
    """
    Poll information_schema at a fixed interval. When any fact table's
    column list differs from the last known snapshot, flag dependent
    metrics as STALE and trigger a metric re-evaluation run.

    Integration points:
      - Calls metric_definition_agent.extract_schema_metadata()
        to obtain the current schema state.
      - Calls metric_definition_agent.generate_metrics_with_gemini()
        to regenerate metrics for drifted tables.
      - Calls metric_definition_agent.save_metrics_to_yaml() and
        save_metrics_to_osi() to persist the updated definitions.
      - Writes a drift_report.yaml entry for every detected change.

    Intended deployment: daemon thread launched alongside mcp_server.py,
    or as a standalone cron job (every 5 minutes in production).

    PostgreSQL alternative (lower latency):
      Instead of polling, subscribe to DDL events via pg_logical replication
      or CREATE EVENT TRIGGER on ddl_command_end to receive instant
      notification of ALTER TABLE / DROP COLUMN without repeated polling.
    """
    # Import here to avoid circular dependency at module load time
    from metric_definition_agent import (
        extract_schema_metadata,
        generate_metrics_with_gemini,
        save_metrics_to_yaml,
        save_metrics_to_osi,
        CHANNEL_GROUPS,
    )

    print(f"[SchemaMonitor] Started — polling every {poll_interval_seconds}s")
    known_schema = extract_schema_metadata()

    while True:
        time.sleep(poll_interval_seconds)
        try:
            current_schema = extract_schema_metadata()
            for table, cols in current_schema.items():
                if table not in CHANNEL_GROUPS:
                    continue   # only monitor governed fact tables
                if table in known_schema and cols != known_schema[table]:
                    print(f"[SchemaMonitor] Drift detected in '{table}' — re-evaluating metrics")
                    _write_drift_report(
                        table,
                        old_cols=[c['column'] for c in known_schema[table]],
                        new_cols=[c['column'] for c in cols],
                    )
                    try:
                        new_metrics = generate_metrics_with_gemini(table, cols)
                        save_metrics_to_yaml(table, new_metrics)
                        save_metrics_to_osi(table, new_metrics)
                        print(f"[SchemaMonitor] Re-evaluation complete for '{table}' "
                              f"— {len(new_metrics)} metrics updated.")
                    except Exception as e:
                        print(f"[SchemaMonitor] Re-evaluation failed for '{table}': {e}")
            known_schema = current_schema
        except Exception as e:
            print(f"[SchemaMonitor] Polling error: {e}")


# ═══════════════════════════════════════════════════════════════════
# MONITOR 2 — Query Log Monitor
# ═══════════════════════════════════════════════════════════════════
def watch_query_log(poll_interval_seconds=QUERY_POLL_INTERVAL):
    """
    Poll pg_stat_statements for aggregation queries whose source
    columns are not yet covered by any registered metric definition.
    Auto-drafts a new metric proposal and routes it through the
    governance workflow (AI validation + confidence triage).

    Integration points:
      - Requires pg_stat_statements extension enabled in PostgreSQL:
          CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
      - Calls governance_agent.add_metric() to route the draft
        proposal through AI validation and confidence-based triage
        (Rec 5 — already implemented).
      - Low-confidence drafts (< 90%) are held in triage_queue.yaml
        for human review; high-confidence ones are auto-approved.

    Intended deployment: scheduled job running every 10 minutes,
    or a daemon thread alongside mcp_server.py.

    Extension: integrate with dbt's query tagging or Cube.js query
    history API as an alternative source of ungoverned query patterns
    when pg_stat_statements is not available.
    """
    from governance_agent import add_metric

    UNGOVERNED_SQL = """
        SELECT
            query,
            calls,
            rows
        FROM pg_stat_statements
        WHERE (
            query ILIKE '%%SUM(%%'
            OR query ILIKE '%%AVG(%%'
            OR query ILIKE '%%COUNT(%%'
        )
        AND query NOT ILIKE '%%pg_stat%%'
        ORDER BY calls DESC
        LIMIT 20
    """

    print(f"[QueryMonitor] Started — polling every {poll_interval_seconds}s")

    while True:
        time.sleep(poll_interval_seconds)
        try:
            conn = _get_db_connection()
            cur  = conn.cursor()
            cur.execute(UNGOVERNED_SQL)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for query, calls, _ in rows:
                print(f"[QueryMonitor] Frequent pattern ({calls}x): {query[:100]}")
                # TODO: parse query to extract table name, column, and aggregation type.
                # Once parsed, call:
                #   add_metric(
                #       table_name = <parsed_table>,
                #       new_metric = {
                #           'metric_name':    <derived_snake_case_name>,
                #           'display_name':   <derived_title>,
                #           'description':    f'Auto-detected from {calls} query executions',
                #           'column':         <parsed_column>,
                #           'type':           <parsed_agg_type>,
                #           'category':       'auto-detected',
                #           'business_rules': 'Pending human review',
                #       },
                #       changed_by = 'QueryLogMonitor/auto',
                #       reason     = f'Column aggregated {calls}x without a registered metric',
                #   )

        except Exception as e:
            print(f"[QueryMonitor] Polling error: {e}")


# ─────────────────────────────────────────────────────────────────
# ENTRY POINT — run both monitors as daemon threads
# ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import threading

    print("=" * 60)
    print("  FUTURE SCOPE MONITORS — Starting (both as daemon threads)")
    print(f"  Schema poll interval : {SCHEMA_POLL_INTERVAL}s")
    print(f"  Query  poll interval : {QUERY_POLL_INTERVAL}s")
    print("=" * 60)

    t1 = threading.Thread(target=watch_schema_changes, daemon=True,
                          name='SchemaChangeMonitor')
    t2 = threading.Thread(target=watch_query_log, daemon=True,
                          name='QueryLogMonitor')

    t1.start()
    t2.start()

    print("Both monitors running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nMonitors stopped.")
