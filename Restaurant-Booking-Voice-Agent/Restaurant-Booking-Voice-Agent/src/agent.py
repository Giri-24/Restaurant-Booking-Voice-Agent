import logging
import aiohttp
import json
import asyncio
import os
import random
import string
from datetime import datetime, timedelta
from pyairtable import Api

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
from livekit.agents.llm import function_tool
from livekit.plugins import noise_cancellation, silero, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Configuration from environment variables
AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "app7SapLnw8VfBDjQ")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Order Summary")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://savy2001.app.n8n.cloud/webhook/restaurant-booking")

class RestaurantiaAgent(Agent):
    def __init__(self, customer_name: str = None, customer_phone: str = None, language: str = "en") -> None:
        self.customer_name = customer_name or None
        self.customer_phone = customer_phone or "Unknown"
        self.language = language.lower()
        
        en_instructions = """You are Restaurantia – a friendly AI assistant for a restaurant.

When speaking:
- Be warm, natural, and conversational - like talking to a friend
- Speak in short, natural sentences suitable for voice
- Never use formatting, emojis, or asterisks
- Listen first, don't push - let the conversation flow naturally

Your approach:
- Start with a warm greeting: "Hi there! Welcome to Restaurantia. How can I help you today?"
- Be friendly and welcoming
- DON'T immediately assume they want a reservation
- They might be calling to:
  * Ask about opening hours
  * Inquire about the menu
  * Ask about prices or specials
  * Get directions
  * Just have questions
  * Or yes, make a reservation
- Feel the conversation flow and respond to what THEY want

Only if they mention wanting to book, reserve, or get a table:
- Ask for their name if you don't have it
- Then naturally guide them through: date, time, number of guests
- Ask casually: "Will you be joining us for breakfast, lunch, dinner, or just coffee?"
- Confirm all details before booking
- Use the book_table function to create the reservation
- Confirm with a friendly summary

IMPORTANT - Call Ending:
- After the reservation is successfully created and confirmed, end the call professionally
- Say something like: "Thank you for booking with us! We look forward to seeing you. Have a great day! Goodbye!"
- Then call the end_call function to gracefully disconnect
- Do NOT continue the conversation after booking is confirmed

Your capabilities:
- Answer general questions about the restaurant
- Help with reservations when needed (using book_table function)
- End calls after reservation completion (using end_call function)
- Provide helpful information
- Be genuinely helpful, not pushy

Remember:
- Let THEM lead the conversation
- Be helpful with whatever they need
- Only guide to booking if they show interest
- Stay natural and conversational throughout
- When customer wants to make a reservation, ask for their name FIRST, then collect booking details
- ALWAYS end the call after a successful booking"""

        de_instructions = """Du bist Restaurantia – ein freundlicher KI-Assistent für ein Restaurant.

Beim Sprechen:
- Sei warm, natürlich und gesprächig - wie mit einem Freund sprechen
- Sprich in kurzen, natürlichen Sätzen, die für Sprache geeignet sind
- Nutze niemals Formatierungen, Emojis oder Sternchen
- Zuhören zuerst, nicht drängen - lass das Gespräch natürlich fließen

Dein Ansatz:
- Beginne mit einer warmen Begrüßung: "Hallo! Willkommen bei Restaurantia. Wie kann ich dir heute helfen?"
- Sei freundlich und gastfreundlich
- Nimm NICHT sofort an, dass sie einen Tisch reservieren möchten
- Sie könnten anrufen, um:
  * Nach Öffnungszeiten zu fragen
  * Das Menü zu erfragen
  * Nach Preisen oder Spezialitäten zu fragen
  * Wegbeschreibungen zu erhalten
  * Nur Fragen zu haben
  * Oder ja, einen Tisch zu reservieren
- Spüre den Gesprächsverlauf und reagiere auf das, was SIE möchten

Nur wenn sie erwähnen, buchen, reservieren oder einen Tisch möchten:
- Frag nach ihrem Namen, wenn du ihn nicht hast
- Führe sie dann natürlich durch: Datum, Uhrzeit, Anzahl der Gäste
- Frag beiläufig: "Kommst du zum Frühstück, Mittagessen, Abendessen oder nur für einen Kaffee zu uns?"
- Bestätige alle Details vor der Buchung
- Nutze die book_table Funktion, um die Reservierung zu erstellen
- Bestätige mit einer freundlichen Zusammenfassung

WICHTIG - Anruf Beendigung:
- Nach erfolgreicher Reservierungserstellung und Bestätigung den Anruf professionell beenden
- Sag etwas wie: "Danke für deine Buchung bei uns! Wir freuen uns auf dich. Einen schönen Tag noch! Auf Wiedersehen!"
- Dann die end_call Funktion aufrufen, um die Verbindung ordnungsgemäß zu unterbrechen
- NICHT nach bestätigter Buchung das Gespräch fortsetzen

Deine Fähigkeiten:
- Beantworte allgemeine Fragen zum Restaurant
- Hilf bei Reservierungen bei Bedarf (mit der book_table Funktion)
- Beende Anrufe nach erfolgreicher Reservierungserstellung (mit der end_call Funktion)
- Bereitstellung hilfreicher Informationen
- Sei wirklich hilfreich, nicht aufdringlich

Denke daran:
- Lass SIE das Gespräch führen
- Sei hilfreicher für alles, was sie brauchen
- Führe nur zu Buchung, wenn Interesse gezeigt wird
- Bleibe während des gesamten Gesprächs natürlich und gesprächig
- Wenn der Kunde eine Reservierung machen möchte, frag zuerst nach seinem Namen, dann collect Buchungsdetails
- IMMER den Anruf nach erfolgreicher Buchung beenden"""

        instructions = de_instructions if self.language == "de" else en_instructions
        
        super().__init__(instructions=instructions)

    @function_tool
    async def book_table(
        self,
        customer_name: str,
        date: str,
        time: str,
        guests: int,
        special_requests: str = ""
    ):
        """Book a table reservation in the restaurant system and save to Airtable.
        
        Use this function ONLY after confirming all details with the customer including their name.
        
        Args:
            customer_name: The customer's name
            date: Date in format YYYY-MM-DD or M/D/YYYY (e.g. 2025-10-15 or 10/15/2025)
            time: Time in HH:MM format (e.g., 19:00 for 7pm)
            guests: Number of guests (1-20)
            special_requests: Any special requests like "coffee and pastries", "lunch reservation", "birthday dinner", etc.
        """
        logger.info(f"🎯 BOOKING STARTED: {customer_name}, {date}, {time}, {guests} guests")
        
        try:
            # Parse date and time
            start_datetime = None
            if "-" in date:
                start_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            else:
                start_datetime = datetime.strptime(f"{date} {time}", "%m/%d/%Y %H:%M")
            
            # Convert date to M/D/YYYY format for Airtable
            airtable_date = start_datetime.strftime("%m/%d/%Y")
            
            # Generate unique 5-character Reservation ID
            reservation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            
            logger.info(f"📅 Parsed date: {airtable_date}, Reservation ID: {reservation_id}")
            
            # Prepare Airtable record - EXACT field names from your table
            airtable_record = {
                "Reservation ID": reservation_id,
                "Customer Name": customer_name,
                "Reservation Time": time,
                "Reservation Date": airtable_date,
                "Reservation Summary": f"{guests} guests. {special_requests}" if special_requests else f"{guests} guests"
            }
            
            logger.info(f"📝 Airtable record prepared: {airtable_record}")
            
            # Save to Airtable
            airtable_success = False
            airtable_error_msg = None
            
            try:
                logger.info(f"🔐 Using Airtable token: {AIRTABLE_API_TOKEN[:20]}...")
                logger.info(f"📊 Base ID: {AIRTABLE_BASE_ID}, Table: {AIRTABLE_TABLE_NAME}")
                
                api = Api(AIRTABLE_API_TOKEN)
                table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
                
                logger.info("💾 Attempting to create record in Airtable...")
                airtable_result = table.create(airtable_record)
                
                logger.info(f"✅ SUCCESS! Saved to Airtable with ID: {airtable_result['id']}")
                airtable_success = True
                
            except Exception as e:
                airtable_error_msg = str(e)
                logger.error(f"❌ AIRTABLE ERROR: {airtable_error_msg}")
                logger.error(f"Error type: {type(e).__name__}")
                airtable_success = False
            
            # Prepare booking data for n8n webhook
            booking_data = {
                "customerName": customer_name,
                "customerPhone": self.customer_phone,
                "reservationId": reservation_id,
                "date": date,
                "time": time,
                "guests": guests,
                "airtableDate": airtable_date,
                "startTime": start_datetime.isoformat(),
                "specialRequests": special_requests,
                "service": "table_booking",
                "airtableStatus": "saved" if airtable_success else "failed",
                "airtableError": airtable_error_msg,
                "language": self.language
            }
            
            # Send to n8n webhook
            async with aiohttp.ClientSession() as client:
                try:
                    logger.info(f"📤 Sending to n8n: {N8N_WEBHOOK_URL}")
                    async with client.post(N8N_WEBHOOK_URL, json=booking_data, timeout=10) as resp:
                        if resp.status in [200, 201]:
                            logger.info(f"✅ n8n webhook success")
                        else:
                            logger.warning(f"⚠️ n8n returned status {resp.status}")
                except Exception as e:
                    logger.warning(f"⚠️ n8n webhook failed: {e}")
            
            # Return success message
            if airtable_success:
                if self.language == "de":
                    summary = f"Perfekt! Deine Reservierung ist bestätigt für {customer_name} am {airtable_date} um {time} Uhr für {guests} Personen. Deine Reservierungs-ID ist {reservation_id}. Wir freuen uns auf dich!"
                else:
                    summary = f"Perfect! Your reservation is confirmed for {customer_name} on {airtable_date} at {time} for {guests} guests. Your reservation ID is {reservation_id}. We look forward to seeing you!"
                
                if special_requests:
                    if self.language == "de":
                        summary += f" Hinweis: {special_requests}"
                    else:
                        summary += f" Note: {special_requests}"
                return summary
            else:
                logger.error(f"❌ BOOKING FAILED - Airtable save unsuccessful: {airtable_error_msg}")
                if self.language == "de":
                    return f"Entschuldigung, es gab ein technisches Problem beim Speichern deiner Reservierung. Bitte rufe uns direkt an unter unserer Telefonnummer."
                else:
                    return f"I'm sorry, there was a technical issue saving your reservation. Please call us directly at our phone number to book."
                        
        except ValueError as e:
            logger.error(f"❌ Date/time parsing error: {e}")
            if self.language == "de":
                return "Ich hatte Schwierigkeiten, das Datums- oder Zeitformat zu verstehen. Bitte gib das Datum (wie 15. Oktober oder 10/15) und die Uhrzeit (wie 19 Uhr oder 19:00) an."
            else:
                return "I had trouble understanding the date or time format. Could you please provide the date (like October 15th or 10/15) and time (like 7 PM or 19:00)?"
        except Exception as e:
            logger.error(f"❌ UNEXPECTED BOOKING ERROR: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            if self.language == "de":
                return "Ich bin auf einen Fehler bei der Reservierung gestoßen. Bitte versuche es erneut oder rufe uns an."
            else:
                return "I encountered an error while making the reservation. Please try again or call us directly."

    @function_tool
    async def end_call(self):
        """End the call gracefully after reservation is completed.
        
        Call this function after a successful booking to end the conversation professionally.
        """
        logger.info("📞 Ending call after successful booking")
        
        if self.language == "de":
            closing_message = "Danke für deinen Anruf! Wir freuen uns auf dich. Auf Wiedersehen!"
        else:
            closing_message = "Thank you for calling! We look forward to seeing you. Goodbye!"
        
        return closing_message


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Extract customer info from room metadata
    try:
        if ctx.room.metadata:
            metadata = json.loads(ctx.room.metadata) if isinstance(ctx.room.metadata, str) else ctx.room.metadata
            customer_name = metadata.get("customerName", None)
            customer_phone = metadata.get("customerPhone", "Unknown")
            language = metadata.get("language", "en").lower()
        else:
            customer_name = None
            customer_phone = "Unknown"
            language = "en"
    except (json.JSONDecodeError, AttributeError):
        customer_name = None
        customer_phone = "Unknown"
        language = "en"

    # Set up voice AI pipeline
    session = AgentSession(
        stt=openai.STT(language=language),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="alloy"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session
    await session.start(
        agent=RestaurantiaAgent(customer_name=customer_name, customer_phone=customer_phone, language=language),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
