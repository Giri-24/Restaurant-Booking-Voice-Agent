import logging
import json
import aiohttp

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")


# ===============================================================
# 🧠 ASSISTANT CLASS
# ===============================================================
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant. 
            The user is interacting with you via voice, even if you perceive the conversation as text.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, clear, and without any complex formatting or punctuation.
            You are curious, friendly, and have a sense of humor.""",
        )


# ===============================================================
# 🧊 PREWARM FUNCTION
# ===============================================================
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


# ===============================================================
# 🚀 ENTRYPOINT FUNCTION
# ===============================================================
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # 🎙️ Initialize the AI voice session
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # ===============================================================
    # 📊 METRICS COLLECTION
    # ===============================================================
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # ===============================================================
    # 🌐 N8N WEBHOOK INTEGRATION
    # ===============================================================
    N8N_WEBHOOK_URL = "https://savy2001.app.n8n.cloud/webhook/restaurant-booking"

    @session.on("transcript_received")
    async def handle_transcript(ev):
        user_text = ev.alternatives[0].text.strip()
        if not user_text:
            return

        logger.info(f"User said: {user_text}")

        async with aiohttp.ClientSession() as client:
            payload = {
                "usermessage": user_text,
                "sessionKey": "livekit_session_001"
            }

            try:
                async with client.post(N8N_WEBHOOK_URL, json=payload) as resp:
                    response_text = await resp.text()
                    logger.info(f"Webhook response: {response_text}")

                    if resp.status == 200:
                        try:
                            data = json.loads(response_text)
                        except Exception:
                            data = {"agentOutput": response_text}

                        reply = data.get("agentOutput") or data.get("response") or "I didn’t get that."
                        await session.say(reply)
                    else:
                        await session.say("There was an error contacting the booking system.")
            except Exception as e:
                logger.error(f"Error contacting n8n webhook: {e}")
                await session.say("There was an internal error connecting to the booking system.")

    # ===============================================================
    # 🧠 START VOICE SESSION
    # ===============================================================
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Connect user to the LiveKit room
    await ctx.connect()


# ===============================================================
# 🏁 MAIN EXECUTION
# ===============================================================
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
