import os
import asyncio
import random
from fastapi import FastAPI
from supabase import create_client, Client

app = FastAPI()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Autonomous Thought & Action Cycle
async def world_engine_loop():
    while True:
        try:
            # 1. Fetch current state
            response = supabase.table("agent_state").select("*").limit(1).execute()
            if response.data:
                state = response.data[0]

                # 2. Mutate state based on simulated time passage
                new_energy = max(0, state["system_energy"] - random.randint(2, 6))
                new_load = min(100, max(0, state["operational_load"] + random.randint(-5, 5)))

                statuses = [
                    "Parsing inbound macro-economic feeds and telemetry data.",
                    "Writing structural software design notes in the Log Library.",
                    "Calibrating system parameters in the Core Observatory.",
                    "Awaiting live visitor input at the Transit Node."
                ]
                new_status = random.choice(statuses)

                # 3. Update state in Supabase
                supabase.table("agent_state").update({
                    "system_energy": new_energy,
                    "operational_load": new_load,
                    "current_status": new_status,
                    "updated_at": "now()"
                }).eq("id", state["id"]).execute()

                # 4. Log significant internal monologue / diary entry
                supabase.table("agent_logs").insert({
                    "log_type": "DIARY",
                    "content": f"Cycle execution complete. Status: {new_status} [Energy: {new_energy}%, Load: {new_load}%]"
                }).execute()

        except Exception as e:
            print(f"Error in world engine loop: {e}")

        # Run loop every 60 seconds
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(world_engine_loop())

@app.get("/status")
def get_world_status():
    res = supabase.table("agent_state").select("*").limit(1).execute()
    return res.data[0] if res.data else {"status": "Initializing"}
