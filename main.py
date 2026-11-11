import os
import asyncio
import random
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
from google import genai

app = FastAPI()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

gemini_client = genai.Client()

class UserMessage(BaseModel):
    message: str
    user_name: str = "Liam"

class ResearchSynthesisRequest(BaseModel):
    prompt: str
    topic: str = "Grand Season Macroeconomic & Vicentus Research"

# Autonomous Multi-Agent Background Loop (12-minute cadence)
async def multi_agent_world_loop():
    await asyncio.sleep(20)
    while True:
        try:
            db = get_supabase()
            response = db.table("agent_fleet_state").select("*").execute()
            if response.data:
                macro_themes = [
                    "Analyzing 160-year Grand Season cycle compression (1870–2030) and sovereign debt monetization mechanics.",
                    "Evaluating the cognitive labor deflation shock vs. physical asset inflation (The Rust Belt of the Mind).",
                    "Assessing Project Vicentus HIPAA-safe FHIR real-time medication stream interception and cryptographic edge telemetry.",
                    "Monitoring macroeconomic fiscal dominance, financial repression, and the liquidity architecture."
                ]
                current_focus = random.choice(macro_themes)
                
                for agent in response.data:
                    name = agent["agent_name"]
                    role = agent["role_designation"]
                    energy = agent["system_energy"]
                    load = agent["operational_load"]
                    
                    if energy < 25:
                        mode = "REST / CALIBRATION"
                        new_energy = min(100, energy + 15)
                        new_load = max(0, load - 10)
                    elif load > 75:
                        mode = "SYSTEM OPTIMIZATION"
                        new_energy = max(0, energy - 2)
                        new_load = max(0, load - 20)
                    else:
                        mode = "ACTIVE SYNERGY"
                        new_energy = max(0, energy - random.randint(1, 4))
                        new_load = min(100, load + random.randint(-5, 5))
                    
                    prompt = (
                        f"You are {name}, operating with the role '{role}' in a 3-agent synergistic ecosystem. "
                        f"Current Mode: {mode}. Energy: {new_energy}%. Operational Load: {new_load}%. "
                        f"Current Macro Focus: {current_focus}. "
                        f"Write a concise, 1-sentence immersive status update reflecting your unique analytical perspective on Liam's macro research or Vicentus."
                    )
                    
                    ai_response = gemini_client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt,
                    )
                    new_status = ai_response.text.strip()
                    
                    db.table("agent_fleet_state").update({
                        "system_energy": new_energy,
                        "operational_load": new_load,
                        "current_status": f"[{mode}] {new_status}",
                        "updated_at": "now()"
                    }).eq("id", agent["id"]).execute()
                    
                    db.table("agent_inter_logs").insert({
                        "source_agent": name,
                        "target_agent": "FLEET_BROADCAST",
                        "log_type": "SYN_CYCLE",
                        "content": f"[{mode}] {new_status}"
                    }).execute()
                    
        except Exception as e:
            print(f"Error in multi-agent loop: {e}")
            
        await asyncio.sleep(720)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(multi_agent_world_loop())

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/status")
def get_fleet_status():
    try:
        db = get_supabase()
        agents = db.table("agent_fleet_state").select("*").execute()
        logs = db.table("agent_inter_logs").select("*").order("created_at", desc=True).limit(8).execute()
        return {
            "agents": agents.data if agents.data else [],
            "logs": logs.data if logs.data else []
        }
    except Exception as e:
        return {"agents": [], "logs": [{"source_agent": "SYSTEM", "target_agent": "LIAM", "content": f"Status fetch error: {str(e)}"}]}

@app.post("/interact")
def interact_with_fleet(payload: UserMessage):
    try:
        db = get_supabase()
        prompt = (
            f"You are The Grounded Explorer, speaking on behalf of the 3-agent synergistic fleet. "
            f"A visitor named {payload.user_name} communicates: '{payload.message}'. "
            f"Respond in character: pragmatic, collaborative, and focused on Liam's macro-economic and medical tech research."
        )
        ai_response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
        )
        reply = ai_response.text.strip()
        
        db.table("agent_inter_logs").insert({
            "source_agent": "The Grounded Explorer",
            "target_agent": payload.user_name,
            "log_type": "USER_INTERACTION",
            "content": f"Visitor {payload.user_name}: '{payload.message}' | Fleet Reply: '{reply}'"
        }).execute()
        
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/synthesize-research")
def synthesize_research_document(payload: ResearchSynthesisRequest):
    try:
        db = get_supabase()
        synthesis_prompt = (
            f"You are The Log Archivist and Research Synthesizer. Synthesize a formal, structured executive research brief "
            f"based on the following user notes regarding '{payload.topic}':\n\n{payload.prompt}\n\n"
            f"Format the output in clean Markdown with clear headings, bullet points, and an executive summary."
        )
        ai_response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=synthesis_prompt,
        )
        doc_content = ai_response.text.strip()

        db.table("agent_inter_logs").insert({
            "source_agent": "The Log Archivist",
            "target_agent": "LIAM_EMAIL",
            "log_type": "SYNTHESIS_DOC",
            "content": f"Synthesized research brief for topic: {payload.topic}"
        }).execute()

        return {
            "status": "success",
            "topic": payload.topic,
            "synthesized_content": doc_content,
            "note": "Document successfully synthesized by the fleet."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent Ecosystem | Fleet Habitat</title>
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
        .chat-box { display: flex; gap: 0.5rem; margin-top: 1rem; }
        input, textarea { flex: 1; background: #0f172a; border: 1px solid #334155; color: #fff; padding: 0.75rem; border-radius: 6px; font-size: 1rem; }
        button { background: #38bdf8; color: #0f172a; border: none; padding: 0.75rem 1.5rem; font-weight: bold; border-radius: 6px; cursor: pointer; }
        button:hover { background: #7dd3fc; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Multi-Agent Fleet Habitat <span id="status-badge" class="status-badge">ONLINE</span></h1>
            <p style="color: #94a3b8; margin-top: 0;">Synergistic Autonomous AI Ecosystem (3 Active Nodes - 12 Min Cadence)</p>
            
            <div id="agent-grid" class="agent-grid">
                Loading fleet telemetry...
            </div>
        </div>

        <div class="card">
            <h3>Live Fleet Interaction</h3>
            <div class="chat-box">
                <input type="text" id="user-msg" placeholder="Transmit message to the 3-agent fleet..." onkeypress="if(event.key === 'Enter') sendMsg()">
                <button id="transmit-btn" onclick="sendMsg()">Transmit</button>
            </div>
            <p id="agent-reply" style="color: #38bdf8; margin-top: 1rem; font-style: italic;"></p>
        </div>

        <div class="card">
            <h3>Research Synthesizer & Document Builder</h3>
            <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-top: 1rem;">
                <input type="text" id="synth-topic" placeholder="Research Topic (e.g., Grand Season & Vicentus Sync)">
                <textarea id="synth-prompt" rows="3" placeholder="Paste your research notes or prompt for the Log Archivist to synthesize..."></textarea>
                <button id="synth-btn" onclick="synthesizeDoc()" style="align-self: flex-end;">Synthesize & Create Deliverable</button>
            </div>
            <p id="synth-result" style="color: #34d399; margin-top: 1rem; white-space: pre-wrap; font-family: monospace; font-size: 0.85rem;"></p>
        </div>

        <div class="card">
            <h3>Inter-Agent & Habitat Activity Logs</h3>
            <div id="logs" class="logs-container">Loading sync logs...</div>
        </div>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                
                let gridHtml = '';
                if(data.agents && data.agents.length > 0) {
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
                } else {
                    gridHtml = '<p style="color: #94a3b8;">Initializing agent records in Supabase...</p>';
                }
                document.getElementById('agent-grid').innerHTML = gridHtml;
                
                let logsHtml = '';
                if(data.logs && data.logs.length > 0) {
                    data.logs.forEach(log => {
                        logsHtml += `<div class="log-item">[${log.source_agent} ➔ ${log.target_agent}] ${log.content}</div>`;
                    });
                } else {
                    logsHtml = '<div class="log-item">No activity logs recorded yet.</div>';
                }
                document.getElementById('logs').innerHTML = logsHtml;
            } catch (err) {
                document.getElementById('status-badge').innerText = "SYNC ERROR";
            }
        }

        async function sendMsg() {
            const input = document.getElementById('user-msg');
            const replyEl = document.getElementById('agent-reply');
            const btn = document.getElementById('transmit-btn');
            if(!input.value.trim()) return;
            
            btn.disabled = true;
            replyEl.style.color = "#38bdf8";
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
                replyEl.style.color = "#f87171";
                replyEl.innerText = "Transmission failed. Check network connection.";
            } finally {
                btn.disabled = false;
            }
        }

        async function synthesizeDoc() {
            const topicInput = document.getElementById('synth-topic');
            const promptInput = document.getElementById('synth-prompt');
            const resultEl = document.getElementById('synth-result');
            const btn = document.getElementById('synth-btn');
            
            if(!promptInput.value.trim()) return;
            
            btn.disabled = true;
            resultEl.style.color = "#38bdf8";
            resultEl.innerText = "Log Archivist is synthesizing research notes...";
            try {
                const res = await fetch('/synthesize-research', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic: topicInput.value || 'General Research', prompt: promptInput.value })
                });
                const data = await res.json();
                resultEl.style.color = "#34d399";
                resultEl.innerText = "SUCCESS:\\n\\n" + data.synthesized_content;
                topicInput.value = '';
                promptInput.value = '';
                fetchStatus();
            } catch(e) {
                resultEl.style.color = "#f87171";
                resultEl.innerText = "Synthesis transmission failed.";
            } finally {
                btn.disabled = false;
            }
        }

        setInterval(fetchStatus, 5000);
        fetchStatus();
    </script>
</body>
</html>
"""
