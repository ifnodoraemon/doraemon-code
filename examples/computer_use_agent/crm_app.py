"""Local CRM demo app for browser-agent execution."""

from __future__ import annotations

import csv
import io
from copy import deepcopy
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

SEED_CUSTOMERS: list[dict[str, Any]] = [
    {
        "id": "cust-001",
        "name": "Acme Manufacturing",
        "month": "2026-05",
        "status": "PENDING",
        "owner": "Mia",
        "lastFollowUp": "2026-05-02",
    },
    {
        "id": "cust-002",
        "name": "Northstar Retail",
        "month": "2026-05",
        "status": "PENDING",
        "owner": "Noah",
        "lastFollowUp": "2026-05-04",
    },
    {
        "id": "cust-003",
        "name": "Bluefin Logistics",
        "month": "2026-05",
        "status": "FOLLOWED_UP",
        "owner": "Mia",
        "lastFollowUp": "2026-05-08",
    },
    {
        "id": "cust-004",
        "name": "Orbit Finance",
        "month": "2026-04",
        "status": "PENDING",
        "owner": "Liam",
        "lastFollowUp": "2026-04-22",
    },
]


class LoginRequest(BaseModel):
    username: str
    password: str


class StatusUpdate(BaseModel):
    status: str


def create_app() -> FastAPI:
    app = FastAPI(title="Computer-Use Agent CRM Demo")
    app.state.customers = deepcopy(SEED_CUSTOMERS)

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return HTML

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"app": "computer-use-agent-crm-demo"}

    @app.post("/api/login")
    async def login(payload: LoginRequest) -> dict[str, Any]:
        if payload.username != "agent@example.com" or payload.password != "demo-password":
            raise HTTPException(status_code=401, detail="invalid credentials")
        return {"ok": True, "user": {"email": payload.username}}

    @app.get("/api/customers")
    async def customers(month: str = "2026-05", status: str = "") -> dict[str, Any]:
        items = [
            customer
            for customer in app.state.customers
            if customer["month"] == month and (not status or customer["status"] == status)
        ]
        return {"items": items}

    @app.patch("/api/customers/{customer_id}/status")
    async def update_status(customer_id: str, payload: StatusUpdate) -> dict[str, Any]:
        if payload.status not in {"PENDING", "FOLLOWED_UP"}:
            raise HTTPException(status_code=400, detail="unsupported status")
        for customer in app.state.customers:
            if customer["id"] == customer_id:
                customer["status"] = payload.status
                customer["lastFollowUp"] = "2026-05-12"
                return {"ok": True, "customer": customer}
        raise HTTPException(status_code=404, detail="customer not found")

    @app.get("/api/export")
    async def export(month: str = "2026-05") -> Response:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "name", "month", "status", "owner", "lastFollowUp"],
        )
        writer.writeheader()
        for customer in app.state.customers:
            if customer["month"] == month:
                writer.writerow(customer)
        return Response(
            output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="crm-export-{month}.csv"'},
        )

    return app


app = create_app()


HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CRM Follow-up Console</title>
  <style>
    body { margin: 0; font-family: Inter, Arial, sans-serif; color: #172033; background: #f5f7fb; }
    header { padding: 18px 28px; background: #172033; color: white; }
    main { max-width: 1080px; margin: 24px auto; padding: 0 20px; }
    .panel { background: white; border: 1px solid #dbe2ef; border-radius: 8px; padding: 20px; }
    .row { display: flex; gap: 12px; align-items: end; flex-wrap: wrap; }
    label { display: grid; gap: 6px; font-size: 13px; font-weight: 700; color: #42526b; }
    input { height: 38px; border: 1px solid #b8c2d6; border-radius: 6px; padding: 0 10px; min-width: 180px; }
    button, a.button { height: 40px; border: 0; border-radius: 6px; padding: 0 14px; background: #1f6feb; color: white; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; }
    button.secondary, a.secondary { background: #42526b; }
    table { width: 100%; border-collapse: collapse; margin-top: 18px; }
    th, td { padding: 11px 10px; border-bottom: 1px solid #e6ebf2; text-align: left; font-size: 14px; }
    th { color: #42526b; font-size: 12px; text-transform: uppercase; }
    .status { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 700; }
    .hidden { display: none; }
    .notice { margin-top: 12px; color: #0a7a43; font-weight: 700; min-height: 22px; }
  </style>
</head>
<body>
  <header><strong>CRM Follow-up Console</strong></header>
  <main>
    <section id="login-panel" class="panel">
      <h1>Sign in</h1>
      <div class="row">
        <label>Email <input data-testid="username" aria-label="Email" value="" /></label>
        <label>Password <input data-testid="password" aria-label="Password" type="password" value="" /></label>
        <button data-testid="login-submit">Sign in</button>
      </div>
      <div id="login-error" class="notice"></div>
    </section>

    <section id="crm-panel" class="panel hidden">
      <h1>Customer follow-up queue</h1>
      <div class="row">
        <label>Month <input data-testid="month-filter" aria-label="Month" value="2026-05" /></label>
        <label>Status <input data-testid="status-filter" aria-label="Status" value="PENDING" /></label>
        <button data-testid="apply-filters">Apply filters</button>
        <a class="button secondary" data-testid="export-csv" href="/api/export?month=2026-05" download>Export CSV</a>
      </div>
      <div id="notice" class="notice"></div>
      <table>
        <thead>
          <tr><th>Name</th><th>Month</th><th>Status</th><th>Owner</th><th>Last follow-up</th><th>Action</th></tr>
        </thead>
        <tbody id="customers"></tbody>
      </table>
    </section>
  </main>
  <script>
    const loginPanel = document.querySelector('#login-panel');
    const crmPanel = document.querySelector('#crm-panel');
    const notice = document.querySelector('#notice');
    const rows = document.querySelector('#customers');
    const monthInput = document.querySelector('[data-testid="month-filter"]');
    const statusInput = document.querySelector('[data-testid="status-filter"]');
    const exportLink = document.querySelector('[data-testid="export-csv"]');

    document.querySelector('[data-testid="login-submit"]').addEventListener('click', async () => {
      const username = document.querySelector('[data-testid="username"]').value;
      const password = document.querySelector('[data-testid="password"]').value;
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
      });
      if (!response.ok) {
        document.querySelector('#login-error').textContent = 'Login failed';
        return;
      }
      loginPanel.classList.add('hidden');
      crmPanel.classList.remove('hidden');
      await loadCustomers();
    });

    document.querySelector('[data-testid="apply-filters"]').addEventListener('click', loadCustomers);

    async function loadCustomers() {
      const month = monthInput.value;
      const status = statusInput.value;
      exportLink.href = `/api/export?month=${encodeURIComponent(month)}`;
      const response = await fetch(`/api/customers?month=${encodeURIComponent(month)}&status=${encodeURIComponent(status)}`);
      const data = await response.json();
      rows.innerHTML = '';
      for (const customer of data.items) {
        const tr = document.createElement('tr');
        tr.setAttribute('data-customer-id', customer.id);
        tr.innerHTML = `
          <td data-field="name">${customer.name}</td>
          <td>${customer.month}</td>
          <td data-field="status" class="status">${customer.status}</td>
          <td>${customer.owner}</td>
          <td>${customer.lastFollowUp}</td>
          <td><button data-testid="mark-followed-${customer.id}">Mark followed up</button></td>
        `;
        tr.querySelector('button').addEventListener('click', async () => {
          await fetch(`/api/customers/${customer.id}/status`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: 'FOLLOWED_UP'})
          });
          notice.textContent = `${customer.name} marked followed up`;
          await loadCustomers();
        });
        rows.appendChild(tr);
      }
      if (data.items.length === 0) {
        rows.innerHTML = '<tr><td colspan="6">No customers match the filters.</td></tr>';
      }
    }
  </script>
</body>
</html>
"""
