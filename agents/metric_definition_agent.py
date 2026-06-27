import os
import json
import yaml
import psycopg2
from google import genai
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY     = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY       = os.getenv('GROQ_API_KEY')
DB_HOST            = os.getenv('DB_HOST', 'localhost')
DB_PORT            = os.getenv('DB_PORT', '5432')
DB_NAME            = os.getenv('DB_NAME', 'tpcds')
DB_USER            = os.getenv('DB_USER', 'cube')
DB_PASS            = os.getenv('DB_PASS', 'cube_pass')
METRICS_PATH       = os.getenv('METRICS_PATH', './metrics')
CUBEJS_MODEL_PATH  = os.getenv('CUBEJS_MODEL_PATH', './cubejs/model')

client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────────────────────────
# REC 1 — CHANNEL GROUPS for cross-table context injection
# Tables in the same group share business semantics and should
# align aggregation types and categories during generation.
# ─────────────────────────────────────────────────────────────────
CHANNEL_GROUPS = {
    'store_sales':     'sales',
    'catalog_sales':   'sales',
    'web_sales':       'sales',
    'store_returns':   'returns',
    'catalog_returns': 'returns',
    'web_returns':     'returns',
    'inventory':       'inventory',
}

def get_peer_context(table_name, generated_so_far):
    """
    Build a context string summarising metrics already generated for
    peer tables in the same channel group.  Injected into the prompt
    so the model can align aggregation types and categories.
    """
    channel = CHANNEL_GROUPS.get(table_name)
    if not channel:
        return ""

    peers = [
        t for t in generated_so_far
        if CHANNEL_GROUPS.get(t) == channel and t != table_name
    ]
    if not peers:
        return ""

    lines = [
        f"\n--- PEER TABLE CONTEXT (channel: {channel}) ---",
        "The following metrics have already been generated for related tables",
        "in the same channel group. Align aggregation types and categories",
        "with these definitions to ensure cross-table consistency:\n"
    ]
    for peer in peers:
        lines.append(f"Table: {peer}")
        for m in generated_so_far[peer][:5]:   # show up to 5 per peer
            lines.append(
                f"  • {m['metric_name']} | type: {m['type']} "
                f"| category: {m['category']}"
            )
        lines.append("")
    lines.append("--- END PEER CONTEXT ---\n")
    return '\n'.join(lines)

# ---------------------------------------------
# 1. DATABASE CONNECTION
# ---------------------------------------------
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# ---------------------------------------------
# 2. EXTRACT SCHEMA METADATA
# ---------------------------------------------
def extract_schema_metadata():
    """Extract all table and column information from PostgreSQL."""
    print("  Connecting to PostgreSQL...")
    conn = get_db_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            t.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable
        FROM information_schema.tables t
        JOIN information_schema.columns c
          ON t.table_name = c.table_name
         AND t.table_schema = c.table_schema
        WHERE t.table_schema = 'public'
          AND t.table_type   = 'BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position
    """)

    rows   = cur.fetchall()
    schema = {}
    for table_name, column_name, data_type, is_nullable in rows:
        schema.setdefault(table_name, []).append({
            'column':   column_name,
            'type':     data_type,
            'nullable': is_nullable
        })

    cur.close()
    conn.close()
    print(f"  Found {len(schema)} tables in PostgreSQL.")
    return schema

# ---------------------------------------------
# 3. GENERATE METRICS  (Rec 1: peer_context injected)
# ---------------------------------------------
def generate_metrics_with_gemini(table_name, columns, peer_context=""):
    """
    Use Groq/Llama to generate metric definitions for a table.
    peer_context (Rec 1): metrics from peer tables in the same channel
    group, injected so the model aligns aggregation types/categories.
    """
    columns_str = '\n'.join(
        [f"  - {col['column']} ({col['type']})" for col in columns]
    )

    prompt = f"""
You are a data analytics expert specialising in semantic layer design for retail analytics.

Given the following database table from a TPC-DS retail dataset:
Table : {table_name}
Columns:
{columns_str}
{peer_context}
Generate a list of meaningful business metrics for this table.
For EACH metric provide exactly these fields:
  metric_name    : snake_case identifier
  display_name   : Human-readable title
  description    : What this metric measures in plain English
  column         : The source column name
  type           : Aggregation type -- one of: sum | count | avg | min | max
  category       : Business category (sales / returns / inventory / customer / finance)
  business_rules : Any filters, conditions or notes (write "None" if not applicable)

Return ONLY a valid JSON array -- no markdown, no extra text.
Example:
[
  {{
    "metric_name":    "total_net_profit",
    "display_name":  "Total Net Profit",
    "description":   "Sum of net profit across all transactions",
    "column":        "ss_net_profit",
    "type":          "sum",
    "category":      "finance",
    "business_rules":"Excludes cancelled orders"
  }}
]
"""

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if response_text.startswith('```'):
        parts         = response_text.split('```')
        response_text = parts[1]
        if response_text.lower().startswith('json'):
            response_text = response_text[4:]

    metrics = json.loads(response_text.strip())
    return metrics

# ---------------------------------------------
# 4. SAVE METRICS TO YAML
# ---------------------------------------------
def save_metrics_to_yaml(table_name, metrics):
    """Persist generated metrics to a YAML file."""
    os.makedirs(METRICS_PATH, exist_ok=True)

    metric_doc = {
        'table':        table_name,
        'generated_at': datetime.now().isoformat(),
        'generated_by': 'MetricDefinitionAgent v1.0',
        'version':      '1.0',
        'metrics':      metrics
    }

    filename = os.path.join(METRICS_PATH, f'{table_name}_metrics.yaml')
    with open(filename, 'w') as f:
        yaml.dump(metric_doc, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"  Saved -> {filename}")
    return filename

# ---------------------------------------------
# 5. UPDATE CUBE.JS MODEL FILE
# ---------------------------------------------
def update_cubejs_model(table_name, metrics):
    """Append AI-generated measures to the existing Cube.js JS model file."""
    cube_name = ''.join(word.capitalize() for word in table_name.split('_'))
    js_file   = os.path.join(CUBEJS_MODEL_PATH, f'{cube_name}.js')

    if not os.path.exists(js_file):
        print(f"  Cube.js model not found: {js_file} -- skipping update.")
        return

    new_measures = []
    for m in metrics:
        measure_js = f"""
    // AUTO-GENERATED: {m['display_name']}
    // {m['description']}
    // Category: {m['category']} | Rules: {m['business_rules']}
    {m['metric_name']}: {{
      sql: `{m['column']}`,
      type: `{m['type']}`,
      title: `{m['display_name']}`
    }}"""
        new_measures.append(measure_js)

    with open(js_file, 'r') as f:
        content = f.read()

    insertion = ',\n'.join(new_measures)
    if 'measures: {' in content:
        insert_marker = content.rfind('}', 0, content.rfind('dimensions:'))
        if insert_marker != -1:
            content = content[:insert_marker] + ',\n' + insertion + '\n  ' + content[insert_marker:]

    with open(js_file, 'w') as f:
        f.write(content)

    print(f"  Updated Cube.js model -> {js_file}")

# ---------------------------------------------
# 6. MAIN AGENT LOOP  (Rec 1: tracks generated_so_far)
# ---------------------------------------------
def run_agent(target_tables=None, update_cubejs=False):
    """Run the Metric Definition Agent."""
    print("\n" + "="*60)
    print("  METRIC DEFINITION AGENT -- Starting")
    print("="*60)

    # Step 1 -- Extract schema
    print("\n[Step 1] Extracting schema metadata...")
    schema = extract_schema_metadata()

    # Default: process fact tables only
    fact_tables = [
        'store_sales', 'catalog_sales', 'web_sales',
        'store_returns', 'catalog_returns', 'web_returns',
        'inventory'
    ]
    tables_to_process = target_tables if target_tables else fact_tables

    results         = {}
    generated_so_far = {}   # Rec 1: accumulates metrics per table for peer context

    for table_name in tables_to_process:
        print(f"\n{'-'*50}")
        print(f"[Step 2] Processing table: {table_name}")

        if table_name not in schema:
            print(f"  Table '{table_name}' not found -- skipping.")
            continue

        print(f"  Columns: {len(schema[table_name])}")

        # Rec 1: build peer context from tables already processed
        peer_context = get_peer_context(table_name, generated_so_far)
        if peer_context:
            channel = CHANNEL_GROUPS.get(table_name, 'unknown')
            print(f"  Peer context injected (channel: {channel}, "
                  f"{len([t for t in generated_so_far if CHANNEL_GROUPS.get(t) == channel])} peer(s))")

        try:
            print("  Calling Groq/Llama to generate metrics...")
            metrics = generate_metrics_with_gemini(
                table_name,
                schema[table_name],
                peer_context=peer_context      # Rec 1
            )
            print(f"  Generated {len(metrics)} metrics.")

            # Step 3 -- Save to YAML
            print("[Step 3] Saving metrics to YAML...")
            save_metrics_to_yaml(table_name, metrics)

            # Step 4 -- Optionally update Cube.js
            if update_cubejs:
                print("[Step 4] Updating Cube.js model...")
                update_cubejs_model(table_name, metrics)

            results[table_name]          = metrics
            generated_so_far[table_name] = metrics   # Rec 1: accumulate

            # Print summary
            print(f"\n  Metrics generated for '{table_name}':")
            for m in metrics:
                print(f"    [OK] {m['display_name']} ({m['type'].upper()}) -- {m['description']}")

        except json.JSONDecodeError as e:
            print(f"  JSON parse error for {table_name}: {e}")
        except Exception as e:
            print(f"  Error processing {table_name}: {e}")

    # Final summary
    print("\n" + "="*60)
    print("  METRIC DEFINITION AGENT -- Completed")
    print(f"  Tables processed : {len(results)}")
    print(f"  Metrics path     : {METRICS_PATH}")
    print("="*60 + "\n")

    return results


# ---------------------------------------------
# ENTRY POINT
# ---------------------------------------------
if __name__ == "__main__":
    run_agent(update_cubejs=False)
