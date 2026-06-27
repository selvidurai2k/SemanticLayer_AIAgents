import os
import yaml
import json
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

load_dotenv()

# Configuration
GROQ_API_KEY  = os.getenv('GROQ_API_KEY')
METRICS_PATH  = os.getenv('METRICS_PATH', './metrics')
REPORTS_PATH  = os.getenv('REPORTS_PATH', './reports')

client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────
# 1. LOAD ALL YAML METRIC FILES
# ─────────────────────────────────────────────
def load_all_metrics():
    """Load all metric YAML files from the metrics folder."""
    all_metrics = {}

    if not os.path.exists(METRICS_PATH):
        print(f"  Metrics path not found: {METRICS_PATH}")
        return all_metrics

    for filename in os.listdir(METRICS_PATH):
        if filename.endswith('_metrics.yaml'):
            filepath = os.path.join(METRICS_PATH, filename)
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            table_name = data.get('table', filename.replace('_metrics.yaml', ''))
            all_metrics[table_name] = data.get('metrics', [])
            print(f"  Loaded: {filename} ({len(all_metrics[table_name])} metrics)")

    return all_metrics

# ─────────────────────────────────────────────
# 2. CHECK NAME CONSISTENCY
# ─────────────────────────────────────────────
def check_name_consistency(all_metrics):
    """Find metrics with same display_name but different definitions."""
    issues = []

    # Group metrics by display_name across all tables
    name_map = defaultdict(list)
    for table, metrics in all_metrics.items():
        for m in metrics:
            name_map[m['display_name'].lower().strip()].append({
                'table':        table,
                'metric_name':  m['metric_name'],
                'display_name': m['display_name'],
                'type':         m['type'],
                'column':       m['column'],
                'category':     m['category']
            })

    for display_name, entries in name_map.items():
        if len(entries) > 1:
            # Check for type mismatches
            types = set(e['type'] for e in entries)
            if len(types) > 1:
                issues.append({
                    'issue_type':   'TYPE_MISMATCH',
                    'severity':     'HIGH',
                    'metric_name':  display_name,
                    'description':  f"Metric '{display_name}' uses different aggregation types across tables",
                    'details':      entries,
                    'tables':       [e['table'] for e in entries],
                    'values':       list(types)
                })

            # Check for category mismatches
            categories = set(e['category'] for e in entries)
            if len(categories) > 1:
                issues.append({
                    'issue_type':   'CATEGORY_MISMATCH',
                    'severity':     'MEDIUM',
                    'metric_name':  display_name,
                    'description':  f"Metric '{display_name}' belongs to different categories across tables",
                    'details':      entries,
                    'tables':       [e['table'] for e in entries],
                    'values':       list(categories)
                })

    return issues

# ─────────────────────────────────────────────
# 3. CHECK MISSING METRICS ACROSS TABLES
# ─────────────────────────────────────────────
def check_missing_metrics(all_metrics):
    """Find metrics present in some tables but missing in similar tables."""
    issues = []

    # Group similar tables
    table_groups = {
        'sales':   ['store_sales', 'catalog_sales', 'web_sales'],
        'returns': ['store_returns', 'catalog_returns', 'web_returns']
    }

    for group_name, tables in table_groups.items():
        available_tables = [t for t in tables if t in all_metrics]
        if len(available_tables) < 2:
            continue

        # Get all metric names per table
        metric_names_per_table = {}
        for table in available_tables:
            metric_names_per_table[table] = set(
                m['display_name'].lower().strip()
                for m in all_metrics[table]
            )

        # Find metrics missing in some tables
        all_names = set()
        for names in metric_names_per_table.values():
            all_names.update(names)

        for metric_name in all_names:
            missing_in = [
                t for t in available_tables
                if metric_name not in metric_names_per_table[t]
            ]
            if missing_in:
                present_in = [
                    t for t in available_tables
                    if metric_name in metric_names_per_table[t]
                ]
                issues.append({
                    'issue_type':  'MISSING_METRIC',
                    'severity':    'MEDIUM',
                    'metric_name': metric_name,
                    'description': f"Metric '{metric_name}' exists in {present_in} but is missing in {missing_in}",
                    'present_in':  present_in,
                    'missing_in':  missing_in,
                    'group':       group_name
                })

    return issues

# ─────────────────────────────────────────────
# 4. CHECK NAMING CONVENTION
# ─────────────────────────────────────────────
def check_naming_conventions(all_metrics):
    """Check that metric_name follows snake_case convention."""
    issues = []

    for table, metrics in all_metrics.items():
        for m in metrics:
            name = m['metric_name']
            # Check snake_case: lowercase, underscores only
            if name != name.lower() or ' ' in name or '-' in name:
                issues.append({
                    'issue_type':  'NAMING_CONVENTION',
                    'severity':    'LOW',
                    'metric_name': name,
                    'table':       table,
                    'description': f"Metric '{name}' in '{table}' does not follow snake_case convention",
                    'suggestion':  name.lower().replace(' ', '_').replace('-', '_')
                })

    return issues

# ─────────────────────────────────────────────
# 5. AI-POWERED CONSISTENCY REVIEW
# ─────────────────────────────────────────────
def ai_consistency_review(all_metrics, issues):
    """Use Groq/Llama to review consistency issues and suggest fixes."""

    issues_summary = json.dumps(issues[:10], indent=2)  # Limit to first 10 for token efficiency

    metrics_summary = {}
    for table, metrics in all_metrics.items():
        metrics_summary[table] = [m['display_name'] for m in metrics]

    prompt = f"""
You are a data governance expert reviewing metric consistency in a retail analytics semantic layer.

The following metrics exist across multiple tables:
{json.dumps(metrics_summary, indent=2)}

The following consistency issues were detected:
{issues_summary}

Please provide:
1. A brief assessment of the overall metric consistency (2-3 sentences)
2. Top 3 most critical issues to fix first
3. Specific recommendations to standardise the metrics

Return ONLY a valid JSON object with this structure:
{{
  "overall_assessment": "...",
  "critical_issues": [
    {{"issue": "...", "recommendation": "..."}}
  ],
  "standardisation_rules": [
    "..."
  ]
}}
"""

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = response.choices[0].message.content.strip()

    # Strip markdown fences
    if response_text.startswith('```'):
        parts         = response_text.split('```')
        response_text = parts[1]
        if response_text.lower().startswith('json'):
            response_text = response_text[4:]

    return json.loads(response_text.strip())

# ─────────────────────────────────────────────
# 6. SAVE CONSISTENCY REPORT
# ─────────────────────────────────────────────
def save_report(all_issues, ai_review, all_metrics):
    """Save the full consistency report to YAML."""
    os.makedirs(REPORTS_PATH, exist_ok=True)

    # Count by severity
    high   = len([i for i in all_issues if i.get('severity') == 'HIGH'])
    medium = len([i for i in all_issues if i.get('severity') == 'MEDIUM'])
    low    = len([i for i in all_issues if i.get('severity') == 'LOW'])

    report = {
        'report_type':    'Metric Consistency Report',
        'generated_at':   datetime.now().isoformat(),
        'generated_by':   'MetricConsistencyAgent v1.0',
        'summary': {
            'total_tables':        len(all_metrics),
            'total_metrics':       sum(len(m) for m in all_metrics.values()),
            'total_issues':        len(all_issues),
            'high_severity':       high,
            'medium_severity':     medium,
            'low_severity':        low,
            'consistency_score':   max(0, 100 - (high * 10 + medium * 5 + low * 2))
        },
        'ai_review':      ai_review,
        'issues':         all_issues
    }

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename  = os.path.join(REPORTS_PATH, f'consistency_report_{timestamp}.yaml')
    with open(filename, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"  Report saved → {filename}")
    return report, filename

# ─────────────────────────────────────────────
# 7. MAIN AGENT LOOP
# ─────────────────────────────────────────────
def run_agent():
    """Run the Metric Consistency Agent."""
    print("\n" + "="*60)
    print("  METRIC CONSISTENCY AGENT — Starting")
    print("="*60)

    # Step 1 — Load metrics
    print("\n[Step 1] Loading metric definitions...")
    all_metrics = load_all_metrics()
    if not all_metrics:
        print("  No metric files found. Run metric_definition_agent.py first!")
        return
    print(f"  Loaded metrics for {len(all_metrics)} tables.")

    # Step 2 — Run consistency checks
    print("\n[Step 2] Running consistency checks...")
    all_issues = []

    print("  Checking name consistency...")
    name_issues = check_name_consistency(all_metrics)
    all_issues.extend(name_issues)
    print(f"  Found {len(name_issues)} name consistency issues.")

    print("  Checking for missing metrics across similar tables...")
    missing_issues = check_missing_metrics(all_metrics)
    all_issues.extend(missing_issues)
    print(f"  Found {len(missing_issues)} missing metric issues.")

    print("  Checking naming conventions...")
    naming_issues = check_naming_conventions(all_metrics)
    all_issues.extend(naming_issues)
    print(f"  Found {len(naming_issues)} naming convention issues.")

    # Step 3 — AI review
    print("\n[Step 3] Running AI-powered consistency review...")
    ai_review = ai_consistency_review(all_metrics, all_issues)
    print("  AI review completed.")

    # Step 4 — Save report
    print("\n[Step 4] Saving consistency report...")
    report, filename = save_report(all_issues, ai_review, all_metrics)

    # Print summary
    print("\n" + "="*60)
    print("  METRIC CONSISTENCY AGENT — Results")
    print("="*60)
    print(f"  Tables analysed  : {report['summary']['total_tables']}")
    print(f"  Total metrics    : {report['summary']['total_metrics']}")
    print(f"  Total issues     : {report['summary']['total_issues']}")
    print(f"  HIGH severity    : {report['summary']['high_severity']}")
    print(f"  MEDIUM severity  : {report['summary']['medium_severity']}")
    print(f"  LOW severity     : {report['summary']['low_severity']}")
    print(f"  Consistency Score: {report['summary']['consistency_score']}/100")

    print("\n  AI Assessment:")
    print(f"  {ai_review.get('overall_assessment', 'N/A')}")

    print("\n  Critical Issues:")
    for i, issue in enumerate(ai_review.get('critical_issues', []), 1):
        print(f"  {i}. {issue.get('issue', '')}")
        print(f"     → {issue.get('recommendation', '')}")

    print("\n  Standardisation Rules:")
    for rule in ai_review.get('standardisation_rules', []):
        print(f"  • {rule}")

    print("\n" + "="*60)
    print(f"  Full report saved to: {filename}")
    print("="*60 + "\n")

    return report


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    run_agent()
