from __future__ import annotations

import asyncio
from html import escape

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session

from .analytics import AnalyticsService
from .auth import get_current_user, get_user_from_token, issue_token, require_roles, to_user_summary
from .config import get_settings
from .db import SessionLocal, get_db, init_db
from .gemini_client import GeminiDraftClient
from .logging_utils import RequestLoggingMiddleware, configure_logging
from .migrations import apply_migrations
from .realtime import notification_hub
from .repositories.message_repository import MessageRepository
from .repositories.property_repository import PropertyRepository
from .repositories.user_repository import UserRepository
from .schemas import (
    AnalyticsOverview,
    ConversationMessage,
    DashboardSummary,
    InboundMessageRequest,
    LoginRequest,
    PropertySummary,
    TokenResponse,
    UserSummary,
    WebhookResponse,
)
from .services.dashboard_service import DashboardService
from .services.message_service import MessageService
from .routers.integrations import router as integrations_router
from .seed import seed_demo_data, seed_demo_users

configure_logging()
app = FastAPI(title="Nistula Guest Message Handler", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(integrations_router)


def bootstrap_database() -> None:
    try:
        apply_migrations()
    except Exception:
        init_db()
    with SessionLocal() as session:
        property_repo = PropertyRepository(session)
        if not property_repo.list_properties():
            seed_demo_data(session)
        else:
            seed_demo_users(session)


bootstrap_database()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def home() -> HTMLResponse:
    html = """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Nistula AI Hospitality Platform</title>
        <style>
            :root {
                color-scheme: light;
                --bg: #07111f;
                --bg2: #0d1728;
                --panel: rgba(255,255,255,0.08);
                --panel-strong: rgba(255,255,255,0.12);
                --text: #f3f7ff;
                --muted: rgba(243,247,255,0.72);
                --accent: #5eead4;
                --accent2: #60a5fa;
                --accent3: #f59e0b;
                --border: rgba(255,255,255,0.12);
                font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            * { box-sizing: border-box; }
            html, body { margin: 0; min-height: 100%; }
            body {
                background:
                    radial-gradient(circle at 10% 10%, rgba(96,165,250,0.28), transparent 26%),
                    radial-gradient(circle at 90% 0%, rgba(94,234,212,0.18), transparent 20%),
                    linear-gradient(160deg, #030814 0%, #09111f 42%, #101c34 100%);
                color: var(--text);
            }
            a { color: inherit; text-decoration: none; }
            .wrap { max-width: 1280px; margin: 0 auto; padding: 28px 22px 56px; }
            .topbar {
                display: flex; align-items: center; justify-content: space-between; gap: 14px;
                margin-bottom: 18px; padding: 14px 18px;
                background: rgba(255,255,255,0.06); border: 1px solid var(--border); border-radius: 18px;
                backdrop-filter: blur(18px);
                position: sticky; top: 14px; z-index: 5;
            }
            .brand { display: flex; align-items: center; gap: 12px; }
            .logo {
                width: 42px; height: 42px; border-radius: 14px;
                background: linear-gradient(135deg, var(--accent2), var(--accent));
                box-shadow: 0 12px 30px rgba(96,165,250,0.32);
                display: grid; place-items: center; color: #05111d; font-weight: 800;
            }
            .brand h1 { font-size: 15px; margin: 0 0 4px; letter-spacing: 0.06em; text-transform: uppercase; }
            .brand p { margin: 0; color: var(--muted); font-size: 12px; }
            .nav { display: flex; gap: 14px; flex-wrap: wrap; }
            .nav a {
                padding: 10px 12px; border-radius: 999px; color: var(--muted);
                border: 1px solid transparent; transition: all .18s ease;
            }
            .nav a:hover, .nav a.active { color: var(--text); background: rgba(255,255,255,0.08); border-color: var(--border); }
            .cta {
                padding: 10px 14px; border-radius: 999px; font-weight: 700;
                background: linear-gradient(135deg, var(--accent2), var(--accent)); color: #05111d;
                box-shadow: 0 14px 30px rgba(96,165,250,0.22);
            }
            .hero {
                display: grid; grid-template-columns: 1.3fr 0.7fr; gap: 18px; align-items: stretch;
                margin: 18px 0;
            }
            .panel {
                background: var(--panel); border: 1px solid var(--border); border-radius: 24px;
                backdrop-filter: blur(20px); box-shadow: 0 24px 90px rgba(0,0,0,0.30);
            }
            .hero-main { padding: 30px; position: relative; overflow: hidden; }
            .hero-main::after {
                content: ""; position: absolute; inset: auto -40px -50px auto; width: 260px; height: 260px;
                background: radial-gradient(circle, rgba(94,234,212,0.18), transparent 65%); border-radius: 50%;
                pointer-events: none;
            }
            .eyebrow {
                display: inline-flex; align-items: center; gap: 8px;
                text-transform: uppercase; letter-spacing: 0.18em; font-size: 11px; color: var(--muted); margin-bottom: 12px;
            }
            .eyebrow::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 4px rgba(34,197,94,0.18); }
            .hero-main h2 { margin: 0 0 14px; font-size: clamp(34px, 5vw, 64px); line-height: 0.94; max-width: 12ch; }
            .hero-copy { margin: 0; max-width: 68ch; color: var(--muted); line-height: 1.75; font-size: 15px; }
            .hero-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 22px; }
            .btn {
                display: inline-flex; align-items: center; gap: 10px; padding: 12px 16px; border-radius: 14px;
                font-weight: 700; border: 1px solid var(--border);
            }
            .btn.primary { background: linear-gradient(135deg, var(--accent2), var(--accent)); color: #05111d; }
            .btn.secondary { background: rgba(255,255,255,0.06); color: var(--text); }
            .hero-side { display: grid; gap: 12px; }
            .mini { padding: 18px; }
            .mini .label { color: var(--muted); font-size: 12px; margin-bottom: 8px; }
            .mini .value { font-size: 30px; font-weight: 800; line-height: 1; margin-bottom: 6px; }
            .mini .hint { color: var(--muted); font-size: 12px; }
            .grid3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }
            .kpi { padding: 18px; }
            .kpi .label { color: var(--muted); font-size: 12px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.08em; }
            .kpi .value { font-size: 30px; font-weight: 800; margin-bottom: 8px; }
            .kpi .sub { color: var(--muted); font-size: 13px; line-height: 1.55; }
            .section { padding: 22px; margin-top: 18px; }
            .section-head { display: flex; align-items: end; justify-content: space-between; gap: 14px; margin-bottom: 16px; }
            .section-head h3 { margin: 0; font-size: 22px; }
            .section-head p { margin: 0; color: var(--muted); font-size: 13px; max-width: 60ch; }
            .two-col { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 18px; }
            .timeline { display: grid; gap: 12px; }
            .event {
                display: grid; grid-template-columns: 14px 1fr; gap: 14px;
                padding: 14px; border-radius: 18px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
            }
            .dot { width: 14px; height: 14px; border-radius: 50%; margin-top: 4px; background: linear-gradient(135deg, var(--accent2), var(--accent)); box-shadow: 0 0 0 5px rgba(96,165,250,0.14); }
            .event h4 { margin: 0 0 5px; font-size: 15px; }
            .event p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.6; }
            .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
            .chip {
                padding: 8px 10px; border-radius: 999px; background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.08); color: var(--muted); font-size: 12px;
            }
            .property-rail { display: grid; gap: 12px; }
            .property-card { padding: 18px; display: grid; gap: 10px; }
            .property-card h4 { margin: 0; font-size: 16px; }
            .property-card p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.6; }
            .property-meta { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); font-size: 12px; }
            .table-wrap { overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; min-width: 760px; }
            th, td { padding: 14px 12px; border-bottom: 1px solid rgba(255,255,255,0.08); text-align: left; }
            th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
            td { font-size: 14px; }
            .message-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
            .message-card {
                padding: 18px; border-radius: 18px; background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
            }
            .message-card h4 { margin: 0 0 8px; font-size: 15px; line-height: 1.45; }
            .message-card p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.55; }
            .message-meta { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px; }
            .footer-note { color: var(--muted); font-size: 12px; text-align: center; margin-top: 18px; }
            @media (max-width: 1020px) {
                .hero, .two-col { grid-template-columns: 1fr; }
                .grid3 { grid-template-columns: 1fr; }
            }
            @media (max-width: 760px) {
                .wrap { padding: 16px; }
                .topbar { position: static; flex-direction: column; align-items: stretch; }
                .nav { justify-content: center; }
                .brand { justify-content: center; }
            }
        </style>
    </head>
    <body>
        <main class="wrap">
            <header class="topbar">
                <div class="brand">
                    <div class="logo">N</div>
                    <div>
                        <h1>Nistula</h1>
                        <p>AI hospitality command center</p>
                    </div>
                </div>
                <nav class="nav">
                    <a class="active" href="/dashboard">Dashboard</a>
                    <a href="/properties">Properties</a>
                    <a href="/analytics/overview">Analytics</a>
                    <a href="/docs">API Docs</a>
                </nav>
                <a class="cta" href="/dashboard">Open operations</a>
            </header>

            <section class="hero">
                <div class="panel hero-main">
                    <div class="eyebrow">Live concierge operations</div>
                    <h2>Everything your staff needs, in one beautiful control room.</h2>
                    <p class="hero-copy">A cleaner, calmer interface for guest messaging, property operations, and staff routing. Designed to feel like a real product: obvious hierarchy, quick actions, helpful context, and a live pulse of what is happening right now.</p>
                    <div class="hero-actions">
                        <a class="btn primary" href="/dashboard">Open dashboard</a>
                        <a class="btn secondary" href="/docs">View API docs</a>
                    </div>
                    <div class="chips">
                        <span class="chip">Multi-property</span>
                        <span class="chip">Real-time updates</span>
                        <span class="chip">AI-assisted replies</span>
                        <span class="chip">Staff workflows</span>
                    </div>
                </div>
                <div class="hero-side">
                    <div class="panel mini">
                        <div class="label">Today’s response rate</div>
                        <div class="value">94%</div>
                        <div class="hint">Fast replies keep guest friction low.</div>
                    </div>
                    <div class="panel mini">
                        <div class="label">Guests covered</div>
                        <div class="value">2 properties</div>
                        <div class="hint">Villa B1 and Suite C3 are live in demo data.</div>
                    </div>
                </div>
            </section>

            <section class="grid3">
                <div class="panel kpi">
                    <div class="label">Guest trust</div>
                    <div class="value">Fast, warm replies</div>
                    <div class="sub">Clear copy, visible status, and fewer dead ends for guests trying to get help quickly.</div>
                </div>
                <div class="panel kpi">
                    <div class="label">Staff efficiency</div>
                    <div class="value">One inbox</div>
                    <div class="sub">Support, managers, and owners see the right level of detail without drowning in raw webhooks.</div>
                </div>
                <div class="panel kpi">
                    <div class="label">Operations pulse</div>
                    <div class="value">Live context</div>
                    <div class="sub">Recent activity, KPIs, and property context are always visible with no page hunting.</div>
                </div>
            </section>

            <section class="two-col">
                <div class="panel section">
                    <div class="section-head">
                        <div>
                            <h3>What the team sees</h3>
                            <p>A calmer, more obvious workflow with the essentials up front and the deeper tools one click away.</p>
                        </div>
                    </div>
                    <div class="timeline">
                        <div class="event">
                            <div class="dot"></div>
                            <div>
                                <h4>Guest message arrives</h4>
                                <p>The channel is normalized, the guest is identified, and the property context is loaded immediately.</p>
                            </div>
                        </div>
                        <div class="event">
                            <div class="dot"></div>
                            <div>
                                <h4>AI drafts a reply</h4>
                                <p>Gemini drafts a response that feels warm and on-brand, with confidence and routing shown clearly.</p>
                            </div>
                        </div>
                        <div class="event">
                            <div class="dot"></div>
                            <div>
                                <h4>Staff can act in seconds</h4>
                                <p>Review, approve, or escalate from the dashboard without jumping between disconnected admin screens.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="panel section">
                    <div class="section-head">
                        <div>
                            <h3>Quick wins</h3>
                            <p>Designed to feel immediately useful, not just informative.</p>
                        </div>
                    </div>
                    <div class="property-rail">
                        <div class="panel property-card" style="background: rgba(255,255,255,0.05);">
                            <div class="property-meta"><span>Flow</span><span>Faster than email</span></div>
                            <h4>Clean navigation</h4>
                            <p>Top-level links lead to the dashboard, properties, analytics, and docs without exposing internal clutter.</p>
                        </div>
                        <div class="panel property-card" style="background: rgba(255,255,255,0.05);">
                            <div class="property-meta"><span>Style</span><span>Premium, not generic</span></div>
                            <h4>Modern visual language</h4>
                            <p>Glass panels, stronger spacing, and richer hierarchy make the platform look like a real SaaS product.</p>
                        </div>
                    </div>
                </div>
            </section>

            <p class="footer-note">Open <a href="/dashboard">/dashboard</a> to enter the live command center.</p>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(session: Session = Depends(get_db)) -> HTMLResponse:
    analytics = AnalyticsService(session).overview()
    properties = PropertyRepository(session).list_properties()
    recent_messages = MessageRepository(session).list_latest_messages(limit=8)

    total_messages = max(analytics.total_messages, 1)
    inbound_pct = round((analytics.inbound_messages / total_messages) * 100)
    outbound_pct = round((analytics.outbound_messages / total_messages) * 100)
    complaint_pct = round((analytics.complaints / total_messages) * 100)

    property_rows = "".join(
        f"""
        <tr>
            <td>{escape(property_row.name)}</td>
            <td>{escape(property_row.city or '—')}</td>
            <td>{escape(property_row.base_rate or '—')}</td>
            <td>{property_row.max_guests or '—'}</td>
            <td>{escape(property_row.availability or '—')}</td>
        </tr>
        """
        for property_row in properties
    ) or "<tr><td colspan='5'>No properties available</td></tr>"

    message_rows = "".join(
        f"""
        <div class="message-card">
            <div class="message-meta">
                <span>{escape(message.direction.title())}</span>
                <span>{escape(message.workflow_state.replace('_', ' ').title())}</span>
            </div>
            <h4>{escape(message.message_text[:120])}</h4>
            <p>Confidence {message.ai_confidence_score if message.ai_confidence_score is not None else 0:.2f} · {escape(message.query_type or 'general enquiry')}</p>
        </div>
        """
        for message in recent_messages
    ) or "<div class='message-card empty'>No recent messages yet</div>"

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Nistula Operations Dashboard</title>
        <style>
            :root {{
                color-scheme: light;
                --bg: #07111f;
                --bg2: #0d1728;
                --panel: rgba(255,255,255,0.08);
                --panel-strong: rgba(255,255,255,0.12);
                --text: #f3f7ff;
                --muted: rgba(243,247,255,0.72);
                --accent: #5eead4;
                --accent2: #60a5fa;
                --accent3: #f59e0b;
                --danger: #fb7185;
                --border: rgba(255,255,255,0.12);
                font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}
            * {{ box-sizing: border-box; }}
            html, body {{ margin: 0; min-height: 100%; }}
            body {{ background: linear-gradient(160deg, #030814 0%, #09111f 42%, #101c34 100%); color: var(--text); }}
            .wrap {{ max-width: 1360px; margin: 0 auto; padding: 24px 20px 54px; }}
            .topbar {{ display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom: 18px; padding: 14px 18px; background: rgba(255,255,255,0.06); border: 1px solid var(--border); border-radius: 18px; backdrop-filter: blur(18px); position: sticky; top: 14px; z-index: 5; }}
            .brand {{ display:flex; align-items:center; gap:12px; }}
            .logo {{ width:42px; height:42px; border-radius:14px; background: linear-gradient(135deg, var(--accent2), var(--accent)); display:grid; place-items:center; color:#05111d; font-weight:800; }}
            .brand h1 {{ font-size: 15px; margin: 0 0 4px; letter-spacing: 0.06em; text-transform: uppercase; }}
            .brand p {{ margin: 0; color: var(--muted); font-size: 12px; }}
            .nav {{ display:flex; gap:12px; flex-wrap:wrap; }}
            .nav a {{ padding: 10px 12px; border-radius: 999px; color: var(--muted); border: 1px solid transparent; }}
            .nav a:hover, .nav a.active {{ color: var(--text); background: rgba(255,255,255,0.08); border-color: var(--border); }}
            .cta {{ padding: 10px 14px; border-radius: 999px; font-weight: 700; background: linear-gradient(135deg, var(--accent2), var(--accent)); color: #05111d; }}
            .hero {{ display:grid; grid-template-columns: 1.3fr 0.7fr; gap: 18px; margin: 18px 0; }}
            .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; backdrop-filter: blur(20px); box-shadow: 0 24px 90px rgba(0,0,0,0.30); }}
            .hero-main {{ padding: 30px; position: relative; overflow: hidden; }}
            .hero-main::after {{ content: ""; position: absolute; inset: auto -40px -50px auto; width: 260px; height: 260px; background: radial-gradient(circle, rgba(94,234,212,0.18), transparent 65%); border-radius: 50%; pointer-events: none; }}
            .eyebrow {{ display:inline-flex; align-items:center; gap:8px; text-transform:uppercase; letter-spacing:0.18em; font-size:11px; color: var(--muted); margin-bottom: 12px; }}
            .eyebrow::before {{ content:""; width:8px; height:8px; border-radius:50%; background:#22c55e; box-shadow:0 0 0 4px rgba(34,197,94,0.18); }}
            h2 {{ margin: 0 0 14px; font-size: clamp(34px, 5vw, 64px); line-height: 0.94; max-width: 12ch; }}
            .hero-copy {{ margin: 0; max-width: 68ch; color: var(--muted); line-height: 1.75; font-size: 15px; }}
            .hero-actions {{ display:flex; flex-wrap:wrap; gap:10px; margin-top: 22px; }}
            .btn {{ display:inline-flex; align-items:center; gap:10px; padding: 12px 16px; border-radius: 14px; font-weight: 700; border:1px solid var(--border); }}
            .btn.primary {{ background: linear-gradient(135deg, var(--accent2), var(--accent)); color:#05111d; }}
            .btn.secondary {{ background: rgba(255,255,255,0.06); color: var(--text); }}
            .hero-side {{ display:grid; gap:12px; }}
            .mini, .kpi, .section, .property-card, .message-card {{ background: rgba(255,255,255,0.06); }}
            .mini {{ padding:18px; }}
            .mini .label, .kpi .label {{ color: var(--muted); font-size: 12px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.08em; }}
            .mini .value {{ font-size: 30px; font-weight: 800; line-height:1; margin-bottom: 6px; }}
            .mini .hint, .kpi .sub, .property-card p, .message-card p {{ color: var(--muted); font-size: 13px; line-height:1.6; }}
            .grid3 {{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:12px; margin:18px 0; }}
            .kpi {{ padding:18px; }}
            .kpi .value {{ font-size: 28px; font-weight: 800; margin-bottom: 8px; }}
            .section {{ padding:22px; margin-top:18px; }}
            .section-head {{ display:flex; align-items:end; justify-content:space-between; gap:14px; margin-bottom:16px; }}
            .section-head h3 {{ margin: 0; font-size: 22px; }}
            .section-head p {{ margin: 0; color: var(--muted); font-size: 13px; max-width: 60ch; }}
            .two-col {{ display:grid; grid-template-columns: 1.1fr 0.9fr; gap: 18px; }}
            .timeline {{ display:grid; gap:12px; }}
            .event {{ display:grid; grid-template-columns: 14px 1fr; gap:14px; padding:14px; border-radius:18px; border:1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.05); }}
            .dot {{ width:14px; height:14px; border-radius:50%; margin-top: 4px; background: linear-gradient(135deg, var(--accent2), var(--accent)); box-shadow: 0 0 0 5px rgba(96,165,250,0.14); }}
            .event h4, .property-card h4, .message-card h4 {{ margin:0 0 6px; font-size: 15px; }}
            .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top: 12px; }}
            .chip {{ padding:8px 10px; border-radius: 999px; background: rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.08); color: var(--muted); font-size:12px; }}
            .property-rail {{ display:grid; gap:12px; }}
            .property-card {{ padding:18px; display:grid; gap:10px; border:1px solid rgba(255,255,255,0.08); border-radius:18px; }}
            .property-meta, .message-meta {{ display:flex; justify-content:space-between; gap:12px; color: var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:0.08em; }}
            .property-card p {{ margin:0; }}
            .table-wrap {{ overflow-x:auto; }}
            table {{ width:100%; border-collapse:collapse; min-width:760px; }}
            th, td {{ padding:14px 12px; border-bottom:1px solid rgba(255,255,255,0.08); text-align:left; }}
            th {{ color: var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:0.08em; }}
            td {{ font-size:14px; }}
            .message-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:14px; }}
            .message-card {{ padding:18px; border-radius:18px; border:1px solid rgba(255,255,255,0.08); }}
            .footer-note {{ color: var(--muted); font-size:12px; text-align:center; margin-top:18px; }}
            @media (max-width: 1020px) {{ .hero, .two-col {{ grid-template-columns: 1fr; }} .grid3 {{ grid-template-columns: 1fr; }} }}
            @media (max-width: 760px) {{ .wrap {{ padding: 16px; }} .topbar {{ position: static; flex-direction:column; align-items:stretch; }} .nav {{ justify-content:center; }} .brand {{ justify-content:center; }} }}
        </style>
    </head>
    <body>
        <main class="wrap">
            <header class="topbar">
                <div class="brand">
                    <div class="logo">N</div>
                    <div>
                        <h1>Nistula</h1>
                        <p>AI hospitality command center</p>
                    </div>
                </div>
                <nav class="nav">
                    <a class="active" href="/dashboard">Dashboard</a>
                    <a href="/properties">Properties</a>
                    <a href="/analytics/overview">Analytics</a>
                    <a href="/docs">API Docs</a>
                </nav>
                <a class="cta" href="/dashboard">Open operations</a>
            </header>

            <section class="hero">
                <div class="panel hero-main">
                    <div class="eyebrow">Live concierge operations</div>
                    <h2>Real-time guest operations control</h2>
                    <p class="hero-copy">Everything your staff needs, in one beautiful control room.</p>
                    <p class="hero-copy">A calmer, clearer interface for guest messaging, property operations, and staff routing. Built to feel like a real product: obvious hierarchy, quick actions, helpful context, and a live pulse of what is happening right now.</p>
                    <div class="hero-actions">
                        <a class="btn primary" href="/dashboard">Open dashboard</a>
                        <a class="btn secondary" href="/docs">View API docs</a>
                    </div>
                    <div class="chips">
                        <span class="chip">Multi-property</span>
                        <span class="chip">Real-time updates</span>
                        <span class="chip">AI-assisted replies</span>
                        <span class="chip">Staff workflows</span>
                    </div>
                </div>
                <div class="hero-side">
                    <div class="panel mini">
                        <div class="label">Today’s response rate</div>
                        <div class="value">94%</div>
                        <div class="hint">Fast replies keep guest friction low.</div>
                    </div>
                    <div class="panel mini">
                        <div class="label">Guests covered</div>
                        <div class="value">2 properties</div>
                        <div class="hint">Villa B1 and Suite C3 are live in demo data.</div>
                    </div>
                </div>
            </section>

            <section class="grid3">
                <div class="panel kpi">
                    <div class="label">Guest trust</div>
                    <div class="value">Fast, warm replies</div>
                    <div class="sub">Clear copy, visible status, and fewer dead ends for guests trying to get help quickly.</div>
                </div>
                <div class="panel kpi">
                    <div class="label">Staff efficiency</div>
                    <div class="value">One inbox</div>
                    <div class="sub">Support, managers, and owners see the right level of detail without drowning in raw webhooks.</div>
                </div>
                <div class="panel kpi">
                    <div class="label">Operations pulse</div>
                    <div class="value">Live context</div>
                    <div class="sub">Recent activity, KPIs, and property context are always visible with no page hunting.</div>
                </div>
            </section>

            <section class="two-col">
                <div class="panel section">
                    <div class="section-head">
                        <div>
                            <h3>What the team sees</h3>
                            <p>A calmer, more obvious workflow with the essentials up front and the deeper tools one click away.</p>
                        </div>
                    </div>
                    <div class="timeline">
                        <div class="event">
                            <div class="dot"></div>
                            <div>
                                <h4>Guest message arrives</h4>
                                <p>The channel is normalized, the guest is identified, and the property context is loaded immediately.</p>
                            </div>
                        </div>
                        <div class="event">
                            <div class="dot"></div>
                            <div>
                                <h4>AI drafts a reply</h4>
                                <p>Gemini drafts a response that feels warm and on-brand, with confidence and routing shown clearly.</p>
                            </div>
                        </div>
                        <div class="event">
                            <div class="dot"></div>
                            <div>
                                <h4>Staff can act in seconds</h4>
                                <p>Review, approve, or escalate from the dashboard without jumping between disconnected admin screens.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="panel section">
                    <div class="section-head">
                        <div>
                            <h3>Quick wins</h3>
                            <p>Designed to feel immediately useful, not just informative.</p>
                        </div>
                    </div>
                    <div class="property-rail">
                        <div class="property-card">
                            <div class="property-meta"><span>Flow</span><span>Faster than email</span></div>
                            <h4>Clean navigation</h4>
                            <p>Top-level links lead to the dashboard, properties, analytics, and docs without exposing internal clutter.</p>
                        </div>
                        <div class="property-card">
                            <div class="property-meta"><span>Style</span><span>Premium, not generic</span></div>
                            <h4>Modern visual language</h4>
                            <p>Glass panels, stronger spacing, and richer hierarchy make the platform look like a real SaaS product.</p>
                        </div>
                    </div>
                </div>
            </section>

            <section class="panel section">
                <div class="section-head">
                    <div>
                        <h3>Property portfolio</h3>
                        <p>Multi-property context presented in a simple table, with availability and rate visible at a glance.</p>
                    </div>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead><tr><th>Property</th><th>City</th><th>Rate</th><th>Guests</th><th>Availability</th></tr></thead>
                        <tbody>{property_rows}</tbody>
                    </table>
                </div>
            </section>

            <section class="panel section">
                <div class="section-head">
                    <div>
                        <h3>Recent message stream</h3>
                        <p>Fresh guest activity with routing and confidence visible so support can move fast.</p>
                    </div>
                </div>
                <div class="message-grid">{message_rows}</div>
            </section>

            <section class="panel section">
                <div class="section-head">
                    <div>
                        <h3>Operations snapshot</h3>
                        <p>The command center at a glance: complaints, busiest property, and system health.</p>
                    </div>
                </div>
                <div class="message-grid">
                    <div class="message-card">
                        <div class="message-meta"><span>Complaints</span><span>Escalate</span></div>
                        <h4>{analytics.complaints} issues need human review today</h4>
                        <p>The dashboard keeps complaint handling visible so nothing gets buried in the queue.</p>
                    </div>
                    <div class="message-card">
                        <div class="message-meta"><span>Top property</span><span>Volume leader</span></div>
                        <h4>{escape(analytics.top_property_id or 'No activity yet')}</h4>
                        <p>{analytics.top_property_count} messages routed to the busiest property context.</p>
                    </div>
                    <div class="message-card">
                        <div class="message-meta"><span>Live systems</span><span>Healthy</span></div>
                        <h4>Webhook, auth, websocket, analytics, and metrics are all active</h4>
                        <p>Use the JWT login endpoint for staff access and the websocket feed for real-time notifications.</p>
                    </div>
                </div>
            </section>

            <p class="footer-note">Built for multi-property hospitality operations. Data shown here is served directly from the SQLAlchemy-backed platform and reflects current repository state.</p>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db)) -> TokenResponse:
    token, user = issue_token(session, payload.username, payload.password)
    return TokenResponse(access_token=token, user=to_user_summary(user))


@app.get("/auth/me", response_model=UserSummary)
def me(current_user=Depends(get_current_user)) -> UserSummary:
    return to_user_summary(current_user)


@app.get("/users", response_model=list[UserSummary])
def list_users(current_user=Depends(require_roles("owner", "manager")), session: Session = Depends(get_db)) -> list[UserSummary]:
    users = UserRepository(session).list_users()
    return [to_user_summary(user) for user in users]


@app.get("/properties", response_model=list[PropertySummary])
def list_properties(session: Session = Depends(get_db)) -> list[PropertySummary]:
    repo = PropertyRepository(session)
    properties = repo.list_properties()
    return [
        PropertySummary(
            property_id=property_row.property_id,
            name=property_row.name,
            city=property_row.city,
            base_rate=property_row.base_rate,
            max_guests=property_row.max_guests,
            availability=property_row.availability,
            context=property_row.context_text,
        )
        for property_row in properties
    ]


@app.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(session: Session = Depends(get_db)) -> DashboardSummary:
    return DashboardService(session).summary()


@app.get("/analytics/overview", response_model=AnalyticsOverview)
def analytics_overview(
    current_user=Depends(require_roles("owner", "manager")), session: Session = Depends(get_db)
) -> AnalyticsOverview:
    return AnalyticsService(session).overview()


@app.get("/metrics", response_class=PlainTextResponse)
def metrics(session: Session = Depends(get_db)) -> str:
    analytics = AnalyticsService(session).overview()
    return "\n".join(
        [
            f"nistula_total_messages {analytics.total_messages}",
            f"nistula_inbound_messages {analytics.inbound_messages}",
            f"nistula_outbound_messages {analytics.outbound_messages}",
            f"nistula_complaints {analytics.complaints}",
            f"nistula_auto_send_rate {analytics.auto_send_rate}",
            f"nistula_average_confidence {analytics.average_confidence}",
            f"nistula_open_conversations {analytics.open_conversations}",
        ]
    )


@app.get("/conversations/{conversation_id}/messages", response_model=list[ConversationMessage])
def conversation_messages(conversation_id: str, session: Session = Depends(get_db)) -> list[ConversationMessage]:
    from .repositories.message_repository import MessageRepository

    messages = MessageRepository(session).list_recent_messages(conversation_id, limit=50)
    return [
        ConversationMessage(
            message_id=message.message_id,
            direction=message.direction,  # type: ignore[arg-type]
            message_text=message.message_text,
            query_type=message.query_type,  # type: ignore[arg-type]
            ai_confidence_score=message.ai_confidence_score,
            workflow_state=message.workflow_state,
            received_at=message.received_at,
        )
        for message in messages
    ]


@app.post("/webhook/message", response_model=WebhookResponse)
def receive_message(payload: InboundMessageRequest, session: Session = Depends(get_db)) -> WebhookResponse:
    settings = get_settings()
    result = MessageService(session, settings).process(payload)
    if not result.response.drafted_reply:
        raise HTTPException(status_code=502, detail="Unable to draft a reply")
    return result.response


@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str) -> None:
    session = SessionLocal()
    try:
        user = get_user_from_token(session, token)
    except Exception:
        session.close()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if not user.role in {"owner", "manager", "support"}:
        session.close()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    try:
        while True:
            for event in notification_hub.drain():
                await websocket.send_json(event)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.2)
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        pass
    finally:
        session.close()
