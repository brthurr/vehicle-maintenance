"""
templates.py
------------
Inline Jinja2 / HTML templates for the Vehicle Maintenance Tracker.
Keeping templates in Python strings avoids a separate template directory
and keeps the project self-contained for easy deployment.
"""

# ──────────────────────────────────────────────────────────────────────────────
# Base layout — all pages extend this via Jinja2 block rendering
# ──────────────────────────────────────────────────────────────────────────────
BASE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{% block title %}Vehicle Maintenance Tracker{% endblock %}</title>
  <style>
    /* ── Reset & tokens ──────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0f1117;
      --surface:   #1a1d27;
      --surface2:  #22263a;
      --border:    #2e3350;
      --accent:    #f97316;
      --accent2:   #fb923c;
      --text:      #e2e8f0;
      --muted:     #8892b0;
      --danger:    #ef4444;
      --success:   #22c55e;
      --warning:   #f59e0b;
      --radius:    10px;
      --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
      --font-body: 'IBM Plex Sans', 'Segoe UI', sans-serif;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-body);
      font-size: 15px;
      line-height: 1.6;
      min-height: 100vh;
    }

    a { color: var(--accent); text-decoration: none; }
    a:hover { color: var(--accent2); text-decoration: underline; }

    /* ── Layout ─────────────────────────────────────────────────── */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 0 2rem;
      display: flex;
      align-items: center;
      gap: 2rem;
      height: 58px;
      position: sticky; top: 0; z-index: 100;
    }
    header .logo {
      font-family: var(--font-mono);
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: -0.5px;
      white-space: nowrap;
    }
    header .logo span { color: var(--muted); font-weight: 400; }
    nav { display: flex; gap: 1.5rem; flex: 1; }
    nav a {
      color: var(--muted);
      font-size: 0.88rem;
      font-weight: 500;
      letter-spacing: 0.3px;
      padding: 4px 0;
      border-bottom: 2px solid transparent;
      transition: color .15s, border-color .15s;
    }
    nav a:hover, nav a.active {
      color: var(--text);
      border-bottom-color: var(--accent);
      text-decoration: none;
    }

    main { max-width: 1100px; margin: 0 auto; padding: 2.5rem 1.5rem; }

    /* ── Cards ───────────────────────────────────────────────────── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .card-header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 1.2rem;
      padding-bottom: .75rem;
      border-bottom: 1px solid var(--border);
    }
    .card-header h2 { font-size: 1rem; font-weight: 600; color: var(--text); }

    /* ── Vehicle grid ────────────────────────────────────────────── */
    .vehicle-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.25rem;
    }
    .vehicle-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem 1.5rem;
      transition: border-color .2s, transform .15s;
      position: relative;
    }
    .vehicle-card:hover { border-color: var(--accent); transform: translateY(-2px); }
    .vehicle-card .vc-name {
      font-size: 1.05rem; font-weight: 700; color: var(--text); margin-bottom: .2rem;
    }
    .vehicle-card .vc-sub {
      font-size: .83rem; color: var(--muted); margin-bottom: .9rem;
    }
    .vehicle-card .vc-badge {
      position: absolute; top: 1rem; right: 1rem;
      font-family: var(--font-mono); font-size: .72rem;
      background: var(--surface2); border: 1px solid var(--border);
      padding: 2px 8px; border-radius: 20px; color: var(--muted);
    }
    .vehicle-card .vc-actions { display: flex; gap: .6rem; margin-top: .8rem; }

    /* ── Tables ──────────────────────────────────────────────────── */
    table {
      width: 100%; border-collapse: collapse;
      font-size: .88rem;
    }
    th {
      text-align: left; padding: .6rem .9rem;
      background: var(--surface2);
      color: var(--muted); font-size: .78rem;
      font-weight: 600; letter-spacing: .05em; text-transform: uppercase;
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: .65rem .9rem;
      border-bottom: 1px solid var(--border);
      color: var(--text);
      vertical-align: middle;
    }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: var(--surface2); }

    /* ── Forms ───────────────────────────────────────────────────── */
    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
    }
    .form-group { display: flex; flex-direction: column; gap: .3rem; }
    .form-group label {
      font-size: .8rem; font-weight: 600; color: var(--muted);
      text-transform: uppercase; letter-spacing: .05em;
    }
    input, select, textarea {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 7px;
      color: var(--text);
      font-family: var(--font-body);
      font-size: .92rem;
      padding: .55rem .8rem;
      outline: none;
      transition: border-color .15s;
      width: 100%;
    }
    input:focus, select:focus, textarea:focus { border-color: var(--accent); }
    textarea { resize: vertical; min-height: 80px; }
    select option { background: var(--surface2); }

    /* ── Buttons ─────────────────────────────────────────────────── */
    .btn {
      display: inline-flex; align-items: center; gap: .4rem;
      padding: .45rem 1rem;
      border-radius: 7px;
      font-size: .87rem; font-weight: 600;
      cursor: pointer; border: 1px solid transparent;
      transition: background .15s, color .15s, border-color .15s;
      font-family: var(--font-body);
    }
    .btn-primary   { background: var(--accent); color: #fff; }
    .btn-primary:hover { background: var(--accent2); color: #fff; text-decoration: none; }
    .btn-secondary { background: var(--surface2); color: var(--text); border-color: var(--border); }
    .btn-secondary:hover { border-color: var(--accent); color: var(--accent); text-decoration: none; }
    .btn-danger    { background: transparent; color: var(--danger); border-color: var(--danger); }
    .btn-danger:hover { background: var(--danger); color: #fff; text-decoration: none; }
    .btn-sm { padding: .3rem .7rem; font-size: .8rem; }

    /* ── Alerts / flash ──────────────────────────────────────────── */
    .flash-list { list-style: none; margin-bottom: 1.25rem; }
    .flash-list li {
      padding: .7rem 1rem;
      border-radius: 7px;
      margin-bottom: .5rem;
      font-size: .9rem;
      border: 1px solid;
    }
    .flash-success { background: #14532d22; border-color: #16a34a55; color: var(--success); }
    .flash-error   { background: #450a0a22; border-color: #dc262655; color: var(--danger); }
    .flash-warning { background: #78350f22; border-color: #d9770655; color: var(--warning); }
    .flash-info    { background: #1e3a5f22; border-color: #3b82f655; color: #60a5fa; }

    /* ── Badges & tags ───────────────────────────────────────────── */
    .badge {
      display: inline-block;
      padding: 2px 9px;
      border-radius: 20px;
      font-size: .76rem; font-weight: 600;
      font-family: var(--font-mono);
    }
    .badge-orange  { background: #7c2d1222; color: var(--accent); border: 1px solid #f9731655; }
    .badge-green   { background: #14532d22; color: var(--success); border: 1px solid #16a34a55; }
    .badge-red     { background: #450a0a22; color: var(--danger);  border: 1px solid #dc262655; }
    .badge-muted   { background: var(--surface2); color: var(--muted); border: 1px solid var(--border); }

    /* ── Misc ────────────────────────────────────────────────────── */
    .page-header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 1.75rem;
    }
    .page-header h1 { font-size: 1.45rem; font-weight: 700; }
    .text-muted { color: var(--muted); }
    .text-sm    { font-size: .85rem; }
    .mt-1 { margin-top: .5rem; }
    .mt-2 { margin-top: 1rem; }
    .mb-2 { margin-bottom: 1rem; }
    .empty-state {
      text-align: center; padding: 3rem 1rem;
      color: var(--muted); font-size: .92rem;
    }
    .empty-state p { margin-bottom: .75rem; }
    hr { border: none; border-top: 1px solid var(--border); margin: 1.25rem 0; }
    .stat-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
    .stat-box {
      flex: 1; min-width: 140px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1rem 1.25rem;
    }
    .stat-box .stat-val {
      font-family: var(--font-mono);
      font-size: 1.5rem; font-weight: 700;
      color: var(--accent);
    }
    .stat-box .stat-label { font-size: .78rem; color: var(--muted); margin-top: .2rem; }
    .overdue-dot {
      display: inline-block; width: 8px; height: 8px;
      border-radius: 50%; background: var(--danger); margin-right: 4px;
    }
  </style>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>
<header>
  <div class="logo">⚙ maint<span>.track</span></div>
  <nav>
    <a href="/">Vehicles</a>
    <a href="/maintenance-types">Service Types</a>
    <a href="/reports">Reports</a>
  </nav>
  <a href="/vehicles/add" class="btn btn-primary btn-sm">+ Add Vehicle</a>
</header>
<main>
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      <ul class="flash-list">
        {% for cat, msg in messages %}
          <li class="flash-{{ cat }}">{{ msg }}</li>
        {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</main>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────────────────────────────────────
DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """{% block content %}
<div class="page-header">
  <h1>Your Vehicles</h1>
  <a href="/vehicles/add" class="btn btn-primary">+ Add Vehicle</a>
</div>

{% if vehicles %}
  <div class="vehicle-grid">
  {% for row in vehicles %}
    {% set v = row.vehicle %}
    <div class="vehicle-card">
      <span class="vc-badge">{{ v.vehicle_type }}</span>
      <div class="vc-name">{{ v.name }}</div>
      <div class="vc-sub">{{ v.year }} {{ v.make }} {{ v.model }}
        {% if v.vin %}&nbsp;·&nbsp;<span style="font-family:var(--font-mono);font-size:.75rem">{{ v.vin }}</span>{% endif %}
      </div>
      <div class="text-sm text-muted">
        <strong style="color:var(--text)">{{ '{:,}'.format(v.mileage) }}</strong> mi
        {% if row.last_log %}
          &nbsp;·&nbsp; Last: <em>{{ row.last_log['type_name'] }}</em> ({{ row.last_log['service_date'] }})
        {% else %}
          &nbsp;·&nbsp; <em>No logs yet</em>
        {% endif %}
      </div>
      {% if row.overdue %}
        <div class="mt-1 text-sm">
          <span class="overdue-dot"></span>
          <span style="color:var(--danger)">{{ row.overdue }} service(s) overdue by mileage</span>
        </div>
      {% endif %}
      <div class="vc-actions">
        <a href="/vehicles/{{ v.id }}" class="btn btn-secondary btn-sm">View</a>
        <a href="/vehicles/{{ v.id }}/log/add" class="btn btn-primary btn-sm">+ Log Service</a>
        <a href="/vehicles/{{ v.id }}/edit" class="btn btn-secondary btn-sm">Edit</a>
      </div>
    </div>
  {% endfor %}
  </div>
{% else %}
  <div class="empty-state">
    <p>No vehicles yet.</p>
    <a href="/vehicles/add" class="btn btn-primary">Add your first vehicle</a>
  </div>
{% endif %}
{% endblock %}""",
)


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle add / edit form
# ──────────────────────────────────────────────────────────────────────────────
VEHICLE_FORM_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """{% block content %}
<div class="page-header">
  <h1>{% if vehicle %}Edit Vehicle{% else %}Add Vehicle{% endif %}</h1>
  <a href="/" class="btn btn-secondary">← Back</a>
</div>
<div class="card">
  <form method="post" enctype="multipart/form-data">
    <div class="form-grid">
      <div class="form-group">
        <label>Nickname *</label>
        <input name="name" value="{{ vehicle.name if vehicle else '' }}" placeholder="e.g. Red Truck" required>
      </div>
      <div class="form-group">
        <label>Make *</label>
        <input name="make" value="{{ vehicle.make if vehicle else '' }}" placeholder="e.g. Ford" required>
      </div>
      <div class="form-group">
        <label>Model *</label>
        <input name="model" value="{{ vehicle.model if vehicle else '' }}" placeholder="e.g. F-150" required>
      </div>
      <div class="form-group">
        <label>Year *</label>
        <input name="year" type="number" min="1885" max="2027"
               value="{{ vehicle.year if vehicle else '' }}" placeholder="2020" required>
      </div>
      <div class="form-group">
        <label>Current Mileage *</label>
        <input name="mileage" type="number" min="0"
               value="{{ vehicle.mileage if vehicle else '0' }}" placeholder="0" required>
      </div>
      <div class="form-group">
        <label>VIN</label>
        <input name="vin" value="{{ vehicle.vin if vehicle and vehicle.vin else '' }}"
               placeholder="Optional" style="font-family:var(--font-mono)">
      </div>
      <div class="form-group">
        <label>Type</label>
        <select name="vehicle_type">
          {% for t in ['Car/Truck', 'Motorcycle', 'ATV/UTV', 'Boat/Marine', 'RV/Motorhome', 'Other'] %}
            <option {% if vehicle and vehicle.vehicle_type == t %}selected{% endif %}>{{ t }}</option>
          {% endfor %}
        </select>
      </div>
    </div>
    <div class="mt-2" style="display:flex;gap:.75rem">
      <button type="submit" class="btn btn-primary">
        {% if vehicle %}Save Changes{% else %}Add Vehicle{% endif %}
      </button>
      <a href="/" class="btn btn-secondary">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}""",
)


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle detail
# ──────────────────────────────────────────────────────────────────────────────
VEHICLE_DETAIL_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """{% block content %}
<div class="page-header">
  <div>
    <h1>{{ vehicle.name }}</h1>
    <div class="text-sm text-muted">
      {{ vehicle.year }} {{ vehicle.make }} {{ vehicle.model }}
      · {{ '{:,}'.format(vehicle.mileage) }} mi
      · {{ vehicle.vehicle_type }}
      {% if vehicle.vin %}&nbsp;· VIN: <span style="font-family:var(--font-mono)">{{ vehicle.vin }}</span>{% endif %}
    </div>
  </div>
  <div style="display:flex;gap:.6rem">
    <a href="/vehicles/{{ vehicle.id }}/log/add" class="btn btn-primary">+ Log Service</a>
    <a href="/vehicles/{{ vehicle.id }}/edit" class="btn btn-secondary">Edit</a>
    <form method="post" action="/vehicles/{{ vehicle.id }}/delete"
          onsubmit="return confirm('Delete this vehicle and ALL its logs?')">
      <button class="btn btn-danger">Delete</button>
    </form>
  </div>
</div>

{% if upcoming %}
<div class="card">
  <div class="card-header"><h2>Upcoming / Scheduled Services</h2></div>
  <table>
    <thead><tr><th>Service</th><th>Next Due Mileage</th><th>Next Due Date</th></tr></thead>
    <tbody>
    {% for u in upcoming %}
      <tr>
        <td>{{ u.type_name }}</td>
        <td>
          {% if u.next_due_miles %}
            {% if u.next_due_miles <= vehicle.mileage %}
              <span class="badge badge-red">OVERDUE — {{ '{:,}'.format(u.next_due_miles) }} mi</span>
            {% else %}
              <span class="badge badge-orange">{{ '{:,}'.format(u.next_due_miles) }} mi</span>
            {% endif %}
          {% else %}—{% endif %}
        </td>
        <td>{{ u.next_due_date or '—' }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% endif %}

<div class="card">
  <div class="card-header">
    <h2>Service History</h2>
    <span class="text-sm text-muted">{{ logs | length }} records</span>
  </div>
  {% if logs %}
  <table>
    <thead>
      <tr><th>Date</th><th>Service</th><th>Mileage</th><th>Cost</th><th>Receipts</th><th></th></tr>
    </thead>
    <tbody>
    {% for log in logs %}
      <tr>
        <td>{{ log.service_date }}</td>
        <td><a href="/log/{{ log.id }}">{{ log.type_name }}</a></td>
        <td style="font-family:var(--font-mono)">{{ '{:,}'.format(log.mileage_at_service) }}</td>
        <td>{% if log.cost %}${{ '%.2f' | format(log.cost) }}{% else %}—{% endif %}</td>
        <td>
          {% if log.receipt_count %}
            <span class="badge badge-muted">{{ log.receipt_count }} file(s)</span>
          {% else %}—{% endif %}
        </td>
        <td style="white-space:nowrap">
          <a href="/log/{{ log.id }}" class="btn btn-secondary btn-sm">View</a>
          <form method="post" action="/log/{{ log.id }}/delete" style="display:inline"
                onsubmit="return confirm('Delete this log?')">
            <button class="btn btn-danger btn-sm">Del</button>
          </form>
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state">
    <p>No service records yet.</p>
    <a href="/vehicles/{{ vehicle.id }}/log/add" class="btn btn-primary">Log first service</a>
  </div>
  {% endif %}
</div>
{% endblock %}""",
)


# ──────────────────────────────────────────────────────────────────────────────
# Add maintenance log
# ──────────────────────────────────────────────────────────────────────────────
LOG_FORM_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """{% block content %}
<div class="page-header">
  <h1>Log Service — {{ vehicle.name }}</h1>
  <a href="/vehicles/{{ vehicle.id }}" class="btn btn-secondary">← Back</a>
</div>
<div class="card">
  <form method="post" enctype="multipart/form-data">
    <div class="form-grid">
      <div class="form-group" style="grid-column: span 2">
        <label>Service Type *</label>
        <select name="type_id" required>
          <option value="">— Select service —</option>
          {% for t in mtypes %}
            <option value="{{ t.id }}">{{ t.name }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="form-group">
        <label>Service Date *</label>
        <input name="service_date" type="date" required>
      </div>
      <div class="form-group">
        <label>Mileage at Service *</label>
        <input name="mileage_at_service" type="number" min="0"
               value="{{ vehicle.mileage }}" required>
      </div>
      <div class="form-group">
        <label>Cost ($)</label>
        <input name="cost" type="number" step="0.01" min="0" placeholder="0.00">
      </div>
      <div class="form-group">
        <label>Next Due Mileage</label>
        <input name="next_due_miles" type="number" min="0" placeholder="Optional">
      </div>
      <div class="form-group">
        <label>Next Due Date</label>
        <input name="next_due_date" type="date">
      </div>
      <div class="form-group">
        <label>Receipt / Photo</label>
        <input name="receipt" type="file" accept=".pdf,.png,.jpg,.jpeg,.gif,.webp">
      </div>
      <div class="form-group" style="grid-column: span 2">
        <label>Notes</label>
        <textarea name="notes" placeholder="Parts used, observations, brand of oil, etc."></textarea>
      </div>
    </div>
    <div class="mt-2" style="display:flex;gap:.75rem">
      <button type="submit" class="btn btn-primary">Save Log</button>
      <a href="/vehicles/{{ vehicle.id }}" class="btn btn-secondary">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}""",
)


# ──────────────────────────────────────────────────────────────────────────────
# Log detail
# ──────────────────────────────────────────────────────────────────────────────
LOG_DETAIL_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """{% block content %}
<div class="page-header">
  <div>
    <h1>{{ log.type_name }}</h1>
    <div class="text-sm text-muted">
      <a href="/vehicles/{{ log.vehicle_id }}">{{ log.vehicle_name }}</a>
      &nbsp;·&nbsp; {{ log.service_date }}
      &nbsp;·&nbsp; {{ '{:,}'.format(log.mileage_at_service) }} mi
    </div>
  </div>
  <div style="display:flex;gap:.6rem">
    <a href="/vehicles/{{ log.vehicle_id }}" class="btn btn-secondary">← Back</a>
    <form method="post" action="/log/{{ log.id }}/delete"
          onsubmit="return confirm('Delete this log entry?')">
      <button class="btn btn-danger">Delete Log</button>
    </form>
  </div>
</div>

<div class="stat-row">
  <div class="stat-box">
    <div class="stat-val">{{ log.service_date }}</div>
    <div class="stat-label">Service Date</div>
  </div>
  <div class="stat-box">
    <div class="stat-val">{{ '{:,}'.format(log.mileage_at_service) }}</div>
    <div class="stat-label">Mileage</div>
  </div>
  <div class="stat-box">
    <div class="stat-val">{% if log.cost %}${{ '%.2f' | format(log.cost) }}{% else %}—{% endif %}</div>
    <div class="stat-label">Cost</div>
  </div>
  {% if log.next_due_miles or log.next_due_date %}
  <div class="stat-box">
    <div class="stat-val" style="font-size:1rem">
      {% if log.next_due_miles %}{{ '{:,}'.format(log.next_due_miles) }} mi{% endif %}
      {% if log.next_due_miles and log.next_due_date %}/{% endif %}
      {% if log.next_due_date %}{{ log.next_due_date }}{% endif %}
    </div>
    <div class="stat-label">Next Due</div>
  </div>
  {% endif %}
</div>

{% if log.notes %}
<div class="card mb-2">
  <div class="card-header"><h2>Notes</h2></div>
  <p style="white-space:pre-wrap">{{ log.notes }}</p>
</div>
{% endif %}

<div class="card">
  <div class="card-header">
    <h2>Receipts & Attachments</h2>
    <span class="text-sm text-muted">{{ receipts | length }} file(s)</span>
  </div>
  {% if receipts %}
  <table>
    <thead><tr><th>Filename</th><th>Uploaded</th><th></th></tr></thead>
    <tbody>
    {% for r in receipts %}
      <tr>
        <td>{{ r.filename }}</td>
        <td>{{ r.uploaded_at }}</td>
        <td style="white-space:nowrap">
          <a href="/receipts/{{ r.id }}/download" class="btn btn-secondary btn-sm">⬇ Download</a>
          <form method="post" action="/receipts/{{ r.id }}/delete" style="display:inline"
                onsubmit="return confirm('Delete this receipt?')">
            <button class="btn btn-danger btn-sm">Del</button>
          </form>
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state"><p>No receipts attached to this log.</p></div>
  {% endif %}
  <hr>
  <form method="post"
        action="/vehicles/{{ log.vehicle_id }}/log/add"
        enctype="multipart/form-data"
        style="display:flex;gap:.75rem;align-items:center;flex-wrap:wrap">
    <input type="file" name="receipt" accept=".pdf,.png,.jpg,.jpeg,.gif,.webp" style="flex:1;min-width:200px">
    <small class="text-muted">(Upload via Log Service form to attach to a new entry)</small>
  </form>
</div>
{% endblock %}""",
)


# ──────────────────────────────────────────────────────────────────────────────
# Maintenance Types
# ──────────────────────────────────────────────────────────────────────────────
TYPES_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """{% block content %}
<div class="page-header">
  <h1>Service Types</h1>
</div>
<div style="display:grid;grid-template-columns:1fr 340px;gap:1.5rem;align-items:start">
  <div class="card">
    <div class="card-header"><h2>All Service Types</h2></div>
    <table>
      <thead>
        <tr><th>Name</th><th>Interval (mi)</th><th>Interval (mo)</th><th></th></tr>
      </thead>
      <tbody>
      {% for t in mtypes %}
        <tr>
          <td>
            {{ t.name }}
            {% if t.description %}
              <div class="text-sm text-muted">{{ t.description }}</div>
            {% endif %}
          </td>
          <td>{{ '{:,}'.format(t.interval_miles) if t.interval_miles else '—' }}</td>
          <td>{{ t.interval_months or '—' }}</td>
          <td>
            <form method="post" action="/maintenance-types/{{ t.id }}/delete"
                  onsubmit="return confirm('Delete this type?')">
              <button class="btn btn-danger btn-sm">Del</button>
            </form>
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="card">
    <div class="card-header"><h2>Add Custom Type</h2></div>
    <form method="post" action="/maintenance-types/add">
      <div class="form-group mb-2">
        <label>Name *</label>
        <input name="name" placeholder="e.g. Coolant Test" required>
      </div>
      <div class="form-group mb-2">
        <label>Description</label>
        <input name="description" placeholder="Optional">
      </div>
      <div class="form-group mb-2">
        <label>Interval Miles</label>
        <input name="interval_miles" type="number" min="0" placeholder="Optional">
      </div>
      <div class="form-group mb-2">
        <label>Interval Months</label>
        <input name="interval_months" type="number" min="0" placeholder="Optional">
      </div>
      <button type="submit" class="btn btn-primary mt-1">Add Type</button>
    </form>
  </div>
</div>
{% endblock %}""",
)


# ──────────────────────────────────────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────────────────────────────────────
REPORTS_TEMPLATE = BASE_TEMPLATE.replace(
    "{% block content %}{% endblock %}",
    """{% block content %}
<div class="page-header">
  <h1>Reports</h1>
  <form method="get" style="display:flex;gap:.5rem;align-items:center">
    <select name="vehicle_id" onchange="this.form.submit()" style="width:auto">
      <option value="">All Vehicles</option>
      {% for v in vehicles %}
        <option value="{{ v.id }}" {% if selected_vehicle_id == v.id %}selected{% endif %}>
          {{ v.name }}
        </option>
      {% endfor %}
    </select>
  </form>
</div>

<div class="stat-row">
  <div class="stat-box">
    <div class="stat-val">{{ log_count }}</div>
    <div class="stat-label">Total Service Records</div>
  </div>
  <div class="stat-box">
    <div class="stat-val">${{ '%.2f' | format(total_cost) }}</div>
    <div class="stat-label">Total Maintenance Cost</div>
  </div>
</div>

{% if cost_by_type %}
<div class="card">
  <div class="card-header"><h2>Cost by Service Type</h2></div>
  <table>
    <thead>
      <tr><th>Service Type</th><th>Times Performed</th><th>Total Cost</th><th>Avg Cost</th></tr>
    </thead>
    <tbody>
    {% for row in cost_by_type %}
      <tr>
        <td>{{ row.name }}</td>
        <td>{{ row.cnt }}</td>
        <td>{% if row.total %}${{ '%.2f' | format(row.total) }}{% else %}—{% endif %}</td>
        <td>{% if row.avg_cost %}${{ '%.2f' | format(row.avg_cost) }}{% else %}—{% endif %}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% endif %}

<div class="card">
  <div class="card-header"><h2>Recent Service Records</h2></div>
  {% if recent_logs %}
  <table>
    <thead>
      <tr><th>Date</th><th>Vehicle</th><th>Service</th><th>Mileage</th><th>Cost</th></tr>
    </thead>
    <tbody>
    {% for log in recent_logs %}
      <tr>
        <td>{{ log.service_date }}</td>
        <td>{{ log.vehicle_name }}</td>
        <td>{{ log.type_name }}</td>
        <td style="font-family:var(--font-mono)">{{ '{:,}'.format(log.mileage_at_service) }}</td>
        <td>{% if log.cost %}${{ '%.2f' | format(log.cost) }}{% else %}—{% endif %}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state"><p>No records yet.</p></div>
  {% endif %}
</div>
{% endblock %}""",
)
