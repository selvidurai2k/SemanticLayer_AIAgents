"""
governed_metric_api.py — Governed Metric Query API
====================================================
Wraps the metric registry and execution layer in a lightweight
HTTP/JSON-RPC server so that downstream BI tools and AI agents can
only access metrics through approved, governed endpoints.

Why this matters:
  Prevents downstream tools from executing arbitrary SQL.  Every
  query is constructed from the approved metric registry — not from
  caller-supplied input — which eliminates SQL injection risk and
  reduces AI hallucination of column names.

Governed endpoints:
  list_metrics      — list all available metrics (optionally filter by table)
  get_metric        — retrieve a single metric definition by name
  query_metric      — return governed SQL for an approved metric (no raw SQL)
  governance_status — return summary of audit log activity

Security:
  Bearer token authentication on every request.
  Full access log written to governance/api_access_log.yaml.

Usage:
  python governed_metric_api.py
  Server starts on http://localhost:8765
"""

import os
import json
import yaml
import hashlib
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
MCP_PORT        = int(os.getenv('MCP_PORT', '8765'))
MCP_TOKEN       = os.getenv('MCP_TOKEN', 'mcp-governed-access-token')
METRICS_PATH    = os.getenv('METRICS_PATH', './metrics')
GOVERNANCE_PATH = os.getenv('GOVERNANCE_PATH', './governance')
ACCESS_LOG_FILE = os.path.join(GOVERNANCE_PATH, 'api_access_log.yaml')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)s  %(message)s'
)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _load_all_metrics():
    """Load every *_metrics.yaml file from the metrics directory."""
    registry = {}
    if not os.path.isdir(METRICS_PATH):
        return registry
    for fname in os.listdir(METRICS_PATH):
        if fname.endswith('_metrics.yaml') and '_osi' not in fname:
            fpath = os.path.join(METRICS_PATH, fname)
            with open(fpath, 'r') as f:
                doc = yaml.safe_load(f)
            if doc and 'metrics' in doc:
                table = doc.get('table', fname.replace('_metrics.yaml', ''))
                for m in doc['metrics']:
                    registry[m['metric_name']] = {**m, '_table': table}
    return registry


def _load_audit_log():
    audit_file = os.path.join(GOVERNANCE_PATH, 'audit_log.yaml')
    if not os.path.exists(audit_file):
        return []
    with open(audit_file, 'r') as f:
        return yaml.safe_load(f) or []


def _write_access_log(entry):
    os.makedirs(GOVERNANCE_PATH, exist_ok=True)
    log = []
    if os.path.exists(ACCESS_LOG_FILE):
        with open(ACCESS_LOG_FILE, 'r') as f:
            log = yaml.safe_load(f) or []
    log.append(entry)
    with open(ACCESS_LOG_FILE, 'w') as f:
        yaml.dump(log, f, default_flow_style=False, sort_keys=False)


def _build_governed_sql(metric):
    """
    Build a governed SQL SELECT from an approved metric definition.
    Returns deterministic SQL constructed from the metric registry —
    prevents raw SQL execution and reduces hallucination risk.
    """
    agg   = metric.get('type', 'sum').upper()
    col   = metric['column']
    table = metric['_table']
    label = metric['metric_name']
    rules = metric.get('business_rules', 'None')

    where_clause = ''
    if rules and rules.lower() not in ('none', ''):
        where_clause = f'\n  -- Business rule: {rules}'

    return (
        f"SELECT\n"
        f"  {agg}({col}) AS {label}\n"
        f"FROM {table}"
        f"{where_clause};"
    )

# ─────────────────────────────────────────────
# REQUEST HANDLER
# ─────────────────────────────────────────────
class MetricAPIHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Suppress default access log — we write our own."""
        pass

    def _send_json(self, status, payload):
        body = json.dumps(payload, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authenticate(self):
        auth = self.headers.get('Authorization', '')
        if auth != f'Bearer {MCP_TOKEN}':
            self._send_json(401, {'error': 'Unauthorized — invalid or missing Bearer token'})
            return False
        return True

    def _record_access(self, method, params, status, client_ip):
        _write_access_log({
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'method':    method,
            'params':    params,
            'status':    status,
        })

    def do_POST(self):
        if self.path != '/mcp':
            self._send_json(404, {'error': 'Not found — POST to /mcp'})
            return

        if not self._authenticate():
            return

        # Read body
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {'error': 'Invalid JSON body'})
            return

        method = req.get('method', '')
        params = req.get('params', {})
        client_ip = self.client_address[0]

        logging.info(f"MCP  {method}  from {client_ip}  params={params}")

        # ── Route ──────────────────────────────
        if method == 'list_metrics':
            result = self._list_metrics(params)

        elif method == 'get_metric':
            result = self._get_metric(params)

        elif method == 'query_metric':
            result = self._query_metric(params)

        elif method == 'governance_status':
            result = self._governance_status()

        else:
            result = {'error': f"Unknown method '{method}'. "
                               f"Available: list_metrics, get_metric, query_metric, governance_status"}
            self._record_access(method, params, 'ERROR', client_ip)
            self._send_json(400, result)
            return

        self._record_access(method, params, 'OK', client_ip)
        self._send_json(200, {'result': result})

    # ── Endpoint implementations ───────────────

    def _list_metrics(self, params):
        """List all metrics, optionally filtered by table name."""
        registry   = _load_all_metrics()
        table_filter = params.get('table')
        if table_filter:
            metrics = [
                {'metric_name': k, 'table': v['_table'],
                 'type': v.get('type'), 'category': v.get('category')}
                for k, v in registry.items()
                if v['_table'] == table_filter
            ]
        else:
            metrics = [
                {'metric_name': k, 'table': v['_table'],
                 'type': v.get('type'), 'category': v.get('category')}
                for k, v in registry.items()
            ]
        return {'total': len(metrics), 'metrics': metrics}

    def _get_metric(self, params):
        """Return full definition of a single metric."""
        name = params.get('metric_name')
        if not name:
            return {'error': 'param metric_name required'}
        registry = _load_all_metrics()
        metric   = registry.get(name)
        if not metric:
            return {'error': f"Metric '{name}' not found in registry"}
        return metric

    def _query_metric(self, params):
        """
        Return governed SQL for an approved metric.
        Builds SQL from the registry definition — never executes
        raw SQL passed by the caller.
        """
        name = params.get('metric_name')
        if not name:
            return {'error': 'param metric_name required'}
        registry = _load_all_metrics()
        metric   = registry.get(name)
        if not metric:
            return {'error': f"Metric '{name}' not found in registry"}
        sql = _build_governed_sql(metric)
        return {
            'metric_name': name,
            'governed_sql': sql,
            'source_table': metric['_table'],
            'aggregation':  metric.get('type'),
            'note': 'SQL generated from approved metric registry — not from caller input',
        }

    def _governance_status(self):
        """Return a summary of governance audit log activity."""
        audit  = _load_audit_log()
        approved = sum(1 for e in audit if e.get('status') == 'APPROVED')
        rejected = sum(1 for e in audit if e.get('status') == 'REJECTED')
        triage   = sum(1 for e in audit if e.get('status') == 'TRIAGE')
        recent   = audit[-5:] if audit else []
        return {
            'total_logged': len(audit),
            'approved':     approved,
            'rejected':     rejected,
            'triage_queue': triage,
            'recent_activity': recent,
        }


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(GOVERNANCE_PATH, exist_ok=True)
    server = HTTPServer(('0.0.0.0', MCP_PORT), MetricAPIHandler)
    logging.info(f"Governed Metric API running on port {MCP_PORT}")
    logging.info(f"Metrics path    : {METRICS_PATH}")
    logging.info(f"Governance path : {GOVERNANCE_PATH}")
    logging.info(f"Access log      : {ACCESS_LOG_FILE}")
    logging.info("Endpoints: list_metrics | get_metric | query_metric | governance_status")
    logging.info("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Governed Metric API stopped.")
