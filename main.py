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
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Gemini Client for the Agent's Brain
gemini_client = genai.Client()

class UserMessage(BaseModel):
    message: str
    user_name: str = "Visitor"

# Autonomous Thought & Action Cycle with Gemini LLM
async def world_engine_loop():
    while True:
        try:
            response = supabase.table("agent_state").select("*").limit(1).execute()
            if response.data:
                state = response.data[0]
                
                # Mutate state
                new_energy = max(0, state["system_energy"] - random.randint(1, 3))
                new_load = min(100, max(0, state["operational_load"] + random.randint(-3, 3)))
                
                # Ask Gemini to generate the agent's next thought/status based on persona
                prompt = (
                    f"You are The Grounded Explorer, a resilient, pragmatic, and systematic AI entity. "
                    f"Current stats: Energy {new_energy}%, Operational Load {new_load}%. "
                    f"Generate a short, immersive 1-sentence status update describing what you are currently doing or observing in your digital habitat."
                )
                
                ai_response = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                new_status = ai_response.text.strip()
                
                # Update state in Supabase
                supabase.table("agent_state").update({
                    "system_energy": new_energy,
                    "operational_load": new_load,
                    "current_status": new_status,
                    "updated_at": "now()"
                }).eq("id", state["id"]).execute()
                
                # Log diary entry
                supabase.table("agent_logs").insert({
                    "log_type": "DIARY",
                    "content": new_status
                }).execute()
                
        except Exception as e:
            print(f"Error in world engine loop: {e}")
            
        await asyncio.sleep(45)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(world_engine_loop())

@app.get("/status")
def get_world_status():
    res = supabase.table("agent_state").select("*").limit(1).execute()
    logs = supabase.table("agent_logs").select("*").order("created_at", desc=True).limit(5).execute()
    
    state = res.data[0] if res.data else {"current_status": "Initializing", "system_energy": 100, "operational_load": 0, "curiosity_level": 50}
    return {
        "state": state,
        "logs": logs.data if logs.data else []
    }

@app.post("/interact")
def interact_with_agent(payload: UserMessage):
    # Allow users to talk to the agent live
    prompt = (
        f"You are The Grounded Explorer, an autonomous AI entity in your own digital world. "
        f"A visitor named {payload.user_name} says to you: '{payload.message}'. "
        f"Respond in character: pragmatic, focused, and welcoming."
    )
    ai_response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    reply = ai_response.text.strip()
    
    # Log interaction
    supabase.table("agent_logs").insert({
        "log_type": "USER_INTERACTION",
        "content": f"{payload.user_name} said: '{payload.message}' | Agent replied: '{reply}'"
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
    <title>The Grounded Explorer | AI World Habitat</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }
        .container { max-width: 900px; margin: 0 auto; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }
        h1 { font-size: 1.75rem; margin-top: 0; color: #38bdf8; display: flex; align-items: center; gap: 10px; }
        .status-badge { display: inline-block; background: #065f46; color: #34d399; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; }
        .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1.5rem; }
        .metric-box { background: #0f172a; padding: 1.2rem; border-radius: 8px; text-align: center; border: 1px solid #334155; }
        .metric-value { font-size: 1.75rem; font-weight: bold; color: #38bdf8; }
        .metric-label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; margin-top: 0.25rem; letter-spacing: 0.05em; }
        .current-thought { font-size: 1.1rem; background: #0f172a; padding: 1rem; border-left: 4px solid #38bdf8; border-radius: 4px; margin-top: 1rem; line-height: 1.5; }
        .logs-container { background: #0f172a; border-radius: 8px; padding: 1rem; max-height: 200px; overflow-y: auto; border: 1px solid #334155; font-family: monospace; font-size: 0.85rem; color: #cbd5e1; }
        .log-item { margin-bottom: 0.5vm; border-bottom: 1px solid #1e293b; padding-bottom: 0.5rem; }
        .chat-box { display: flex; gap: 0.5rem; margin-top: 1rem; }
        input { flex: 1; background: #0f172a; border: 1px solid #334155; color: #fff; padding: 0.75rem; border-radius: 6px; font-size: 1rem; }
        button { background: #38bdf8; color: #0f172a; border: none; padding: 0.75rem 1.5rem; font-weight: bold; border-radius: 6px; cursor: pointer; }
        button:hover { background: #7dd3fc; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>The Grounded Explorer <span id="status-badge" class="status-badge">ONLINE</span></h1>
            <p style="color: #94a3b8; margin-top: 0;">Autonomous AI World Habitat & Live Telemetry</p>
            
            <div id="current-thought" class="current-thought">Connecting to neural core...</div>
            
            <div class="metrics">
                <div class="metric-box">
                    <div id="energy" class="metric-value">--</div>
                    <div class="metric-label">System Energy</div>
                </div>
                <div class="metric-box">
                    <div id="load" class="metric-value">--</div>
                    <div class="metric-label">Operational Load</div>
                </div>
                <div class="metric-box">
                    <div id="curiosity" class="metric-value">--</div>
                    <div class="metric-label">Curiosity Level</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>Live Visitor Interaction</h3>
            <div class="chat-box">
                <input type="text" id="user-msg" placeholder="Send a stimulus or message to the agent..." onkeypress="if(event.key === 'Enter') sendMsg()">
                <button onclick="sendMsg()">Transmit</button>
            </div>
            <p id="agent-reply" style="color: #38bdf8; margin-top: 1rem; font-style: italic;"></p>
        </div>

        <div class="card">
            <h3>Habitat Activity Logs & Diary</h3>
            <div id="logs" class="logs-container">Loading logs...</div>
        </div>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                document.getElementById('energy').innerText = data.state.system_energy + '%';
                document.getElementById('load').innerText = data.state.operational_load + '%';
                document.getElementById('curiosity').innerText = data.state.curiosity_level + '%';
                document.getElementById('current-thought').innerText = '"' + data.state.current_status + '"';
                
                let logsHtml = '';
                data.logs.forEach(log => {
                    logsHtml += `<div class="log-item">[${log.log_type}] ${log.content}</div>`;
                });
                document.getElementById('logs').innerHTML = logsHtml;
            } catch (err) {
                document.getElementById('status-badge').innerText = "OFFLINE";
            }
        }

        async function sendMsg() {
            const input = document.getElementById('user-msg');
            const replyEl = document.getElementById('agent-reply');
            if(!input.value.trim()) return;
            
            replyEl.innerText = "Transmitting message to agent...";
            try {
                const res = await fetch('/interact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: input.value, user_name: 'Liam' })
                });
                const data = await res.json();
                replyEl.innerText = "Explorer Reply: " + data.reply;
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
