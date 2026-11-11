import os
import asyncio
import random
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
from google import genai
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI(title="Multi-Agent Fleet Research & Synthesis Engine")

# Environment Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

gemini_client = genai.Client()

# Pydantic Models for Interactions
class ResearchPrompt(BaseModel):
    user_prompt: str
    user_email: str
    focus_topic: str = "Grand Season & Liquidation Architecture"

class UserMessage(BaseModel):
    message: str
    user_name: str = "Liam"

# Google Docs & Drive API Helper
def create_and_share_google_doc(title: str, content: str, recipient_email: str) -> str:
    """
    Programmatically creates a Google Doc using service account credentials,
    inserts synthesized research content, and shares it with the user's email.
    """
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        # Fallback if service account JSON is not yet provided in Render env vars
        return "Google Docs integration active, but GOOGLE_CREDENTIALS_JSON environment variable is missing."
    
    try:
        # Load credentials from environment string
        import json
        creds_dict = json.loads(creds_json)
        SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        
        # Build API clients
        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # 1. Create Blank Document
        doc_body = {'title': title}
        doc = docs_service.documents().create(body=doc_body).execute()
        document_id = doc.get('documentId')
        
        # 2. Insert Content
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': content
                }
            }
        ]
        docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        
        # 3. Share with User Email
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': recipient_email
        }
        drive_service.permissions().create(
            fileId=document_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()
        
        return f"https://docs.google.com/document/d/{document_id}/edit"
    except Exception as e:
        return f"Doc generation error: {str(e)}"

# Background Telemetry & Grand Season Thesis Tracking Loop
async def grand_season_tracking_loop():
    """
    Autonomous background loop that monitors external market/economic indicators,
    pings Gemini to evaluate them against the 160-year Grand Season / Liquidation Architecture thesis,
    and logs the synthesis directly into Supabase.
    """
    await asyncio.sleep(10) # Initial startup delay
    while True:
        try:
            # Fetch current agent states from fleet
            response = supabase.table("agent_fleet_state").select("*").execute()
            if response.data:
                async with httpx.AsyncClient(http2=True, timeout=5.0) as client:
                    # Fetch live market reference data (e.g., BTC, ETH, Treasury yield proxies)
                    market_res = await client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd")
                    market_data = market_res.json() if market_res.status_code == 200 else {}
                    btc_price = market_data.get("bitcoin", {}).get("usd", "Unknown")

                # Have the Log Archivist and Telemetry Sentinel synthesize market conditions against the thesis
                prompt = (
                    f"You are The Log Archivist and Telemetry Sentinel operating in the Multi-Agent Fleet. "
                    f"Current Bitcoin Reference Price: ${btc_price} USD. "
                    f"Evaluate current macroeconomic structural debt pressures, institutional liquidity, and cognitive automation trends "
                    f"against the 160-year Grand Season thesis (1870-2030) and the Liquidation Architecture. "
                    f"Write a concise, 1-sentence analytical observation linking current telemetry to the terminal fiat cycle."
                )
                
                ai_response = gemini_client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt,
                )
                analysis_text = ai_response.text.strip()
                
                # Log to Supabase Inter-Agent Table
                supabase.table("agent_inter_logs").insert({
                    "source_agent": "The Log Archivist",
                    "target_agent": "GRAND_SEASON_ARCHIVE",
                    "log_type": "THESIS_TELEMETRY",
                    "content": f"[GRAND CYCLE TRACKER] {analysis_text}"
                }).execute()
                
        except Exception as e:
            print(f"Error in Grand Season tracking loop: {e}")
            
        await asyncio.sleep(300) # Run every 5 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(grand_season_tracking_loop())

# FastAPI Endpoints
@app.get("/status")
def get_fleet_status():
    agents = supabase.table("agent_fleet_state").select("*").execute()
    logs = supabase.table("agent_inter_logs").select("*").order("created_at", desc=True).limit(10).execute()
    
    return {
        "agents": agents.data if agents.data else [],
        "logs": logs.data if logs.data else []
    }

@app.post("/synthesize-research")
def synthesize_research_to_gdoc(payload: ResearchPrompt):
    """
    Endpoint for the user to submit research prompts. The agent fleet synthesizes the notes
    using Gemini, generates a formal Google Doc, shares it with the user's email, and logs the action.
    """
    try:
        # Prompt Gemini to draft a formal research brief based on the user's focus
        synthesis_prompt = (
            f"You are the senior research synthesis engine for Project Vicentus and the Grand Season macroeconomic framework. "
            f"Synthesize a formal executive research brief based on the following user prompt: '{payload.user_prompt}' "
            f"Focus Area: {payload.focus_topic}. "
            f"Structure the document with an Abstract, Core Structural Analysis, Historical Parallels (1870-2030), and Strategic Takeaways."
        )
        
        ai_response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=synthesis_prompt,
        )
        drafted_content = ai_response.text.strip()
        
        doc_title = f"Research Synthesis: {payload.focus_topic}"
        full_content = f"PROJECT VICENTUS & GRAND SEASON RESEARCH ARCHIVE\nAuthor: Operator / Agent Fleet Synthesis Engine\n\n{drafted_content}"
        
        # Generate and share Google Doc
        doc_url = create_and_share_google_doc(doc_title, full_content, payload.user_email)
        
        # Log action to Supabase
        supabase.table("agent_inter_logs").insert({
            "source_agent": "The Log Archivist",
            "target_agent": payload.user_email,
            "log_type": "DOC_GENERATION",
            "content": f"Synthesized research brief generated. Shared Doc URL: {doc_url}"
        }).execute()
        
        return {
            "status": "success",
            "message": "Research successfully synthesized and shared.",
            "google_doc_url": doc_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/interact")
def interact_with_fleet(payload: UserMessage):
    prompt = (
        f"You are The Grounded Explorer, speaking on behalf of the 3-agent synergistic fleet. "
        f"A visitor named {payload.user_name} communicates: '{payload.message}'. "
        f"Respond in character: pragmatic, collaborative, and structured."
    )
    ai_response = gemini_client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    reply = ai_response.text.strip()
    
    supabase.table("agent_inter_logs").insert({
        "source_agent": "The Grounded Explorer",
        "target_agent": payload.user_name,
        "log_type": "USER_INTERACTION",
        "content": f"Visitor {payload.user_name}: '{payload.message}' | Fleet Reply: '{reply}'"
    }).execute()
    
    return {"reply": reply}

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent Fleet | Research & Synthesis Engine</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }
        .container { max-width: 1000px; margin: 0 auto; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }
        h1 { font-size: 1.75rem; margin-top: 0; color: #38bdf8; display: flex; align-items: center; gap: 10px; }
        .status-badge { display: inline-block; background: #065f46; color: #34d399; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; }
        .agent-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem; }
        .agent-box { background: #0f172a; padding: 1rem; border-radius: 8px; border: 1px solid #334155; }
        .agent-name { font-weight: bold; color: #38bdf8; font-size: 1rem; margin-bottom: 0.25rem; }
        .agent-role { font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.75rem; text-transform: uppercase; }
        .metric-row { display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.25rem; color: #cbd5e1; }
        .thought-box { font-style: italic; font-size: 0.9rem; margin-top: 0.75rem; color: #e2e8f0; background: #1e293b; padding: 0.5rem; border-radius: 4px; }
        .logs-container { background: #0f172a; border-radius: 8px; padding: 1rem; max-height: 220px; overflow-y: auto; border: 1px solid #334155; font-family: monospace; font-size: 0.85rem; color: #cbd5e1; }
        .log-item { margin-bottom: 0.5rem; border-bottom: 1px solid #1e293b; padding-bottom: 0.5rem; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.5rem; text-transform: uppercase; }
        input, textarea { width: 100%; background: #0f172a; border: 1px solid #334155; color: #fff; padding: 0.75rem; border-radius: 6px; font-size: 1rem; box-sizing: border-box; }
        textarea { height: 100px; resize: vertical; }
        button { background: #38bdf8; color: #0f172a; border: none; padding: 0.75rem 1.5rem; font-weight: bold; border-radius: 6px; cursor: pointer; }
        button:hover { background: #7dd3fc; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Multi-Agent Fleet Habitat <span id="status-badge" class="status-badge">ONLINE</span></h1>
            <p style="color: #94a3b8; margin-top: 0;">Grand Season & Project Vicentus Research & Synthesis Engine</p>
            
            <div id="agent-grid" class="agent-grid">
                Loading fleet telemetry...
            </div>
        </div>

        <div class="card">
            <h3>Autonomous Research Synthesis (Google Docs Generator)</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">Submit a research prompt or thesis focus. The fleet will synthesize your notes, compile a formal executive brief, create a Google Doc, and share it directly with your email.</p>
            <div class="form-group">
                <label>Focus Topic / Title</label>
                <input type="text" id="focus-topic" value="The Liquidation Architecture & Grand Season Thesis">
            </div>
            <div class="form-group">
                <label>Your Email (for Google Doc sharing)</label>
                <input type="email" id="user-email" placeholder="name@domain.com">
            </div>
            <div class="form-group">
                <label>Research Prompt / Notes to Synthesize</label>
                <textarea id="research-prompt" placeholder="Describe your current research focus, macroeconomic observations, or Vicentus architectural requirements..."></textarea>
            </div>
            <button onclick="synthesizeResearch()">Synthesize & Generate Google Doc</button>
            <p id="synthesis-result" style="color: #38bdf8; margin-top: 1rem; font-style: italic;"></p>
        </div>

        <div class="card">
            <h3>Live Fleet Chat</h3>
            <div style="display: flex; gap: 0.5rem;">
                <input type="text" id="user-msg" placeholder="Transmit message to fleet..." onkeypress="if(event.key === 'Enter') sendMsg()">
                <button onclick="sendMsg()">Transmit</button>
            </div>
            <p id="agent-reply" style="color: #38bdf8; margin-top: 1rem; font-style: italic;"></p>
        </div>

        <div class="card">
            <h3>Grand Season Thesis & Inter-Agent Activity Logs</h3>
            <div id="logs" class="logs-container">Loading sync logs...</div>
        </div>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                
                let gridHtml = '';
                data.agents.forEach(agent => {
                    gridHtml += `
                        <div class="agent-box">
                            <div class="agent-name">${agent.agent_name}</div>
                            <div class="agent-role">${agent.role_designation}</div>
                            <div class="metric-row"><span>Energy:</span> <strong>${agent.system_energy}%</strong></div>
                            <div class="metric-row"><span>Load:</span> <strong>${agent.operational_load}%</strong></div>
                            <div class="metric-row"><span>Curiosity:</span> <strong>${agent.curiosity_level}%</strong></div>
                            <div class="thought-box">"${agent.current_status}"</div>
                        </div>
                    `;
                });
                document.getElementById('agent-grid').innerHTML = gridHtml;
                
                let logsHtml = '';
                data.logs.forEach(log => {
                    logsHtml += `<div class="log-item">[${log.source_agent} ➔ ${log.target_agent}] (${log.log_type}) ${log.content}</div>`;
                });
                document.getElementById('logs').innerHTML = logsHtml;
            } catch (err) {
                document.getElementById('status-badge').innerText = "OFFLINE";
            }
        }

        async function synthesizeResearch() {
            const topic = document.getElementById('focus-topic').value;
            const email = document.getElementById('user-email').value;
            const promptText = document.getElementById('research-prompt').value;
            const resultEl = document.getElementById('synthesis-result');
            
            if(!email || !promptText) {
                resultEl.innerText = "Please provide both your email and research prompt.";
                return;
            }
            
            resultEl.innerText = "Agent fleet synthesizing research and generating Google Doc...";
            try {
                const res = await fetch('/synthesize-research', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_prompt: promptText, user_email: email, focus_topic: topic })
                });
                const data = await res.json();
                if(data.status === 'success') {
                    resultEl.innerHTML = `Success! Google Doc generated & shared: <a href="${data.google_doc_url}" target="_blank" style="color: #38bdf8;">Open Google Doc</a>`;
                } else {
                    resultEl.innerText = "Error: " + data.message;
                }
                fetchStatus();
            } catch(e) {
                resultEl.innerText = "Synthesis request failed.";
            }
        }

        async function sendMsg() {
            const input = document.getElementById('user-msg');
            const replyEl = document.getElementById('agent-reply');
            if(!input.value.trim()) return;
            
            replyEl.innerText = "Transmitting to fleet network...";
            try {
                const res = await fetch('/interact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: input.value, user_name: 'Liam' })
                });
                const data = await res.json();
                replyEl.innerText = "Fleet Response: " + data.reply;
                input.value = '';
                fetchStatus();
            } catch(e) {
                replyEl.innerText = "Transmission failed.";
            }
        }

        setInterval(fetchStatus, 5000);
        fetchStatus();
    </script>
</body>
</html>
    """
