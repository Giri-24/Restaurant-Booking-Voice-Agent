# Big Berlin Hackathon 2025 - https://techeurope.notion.site/big-berlin-hack-manual

# Restaurantia Voice AI Agent

A bilingual (English/German) AI voice reservation agent for restaurants, built with LiveKit Agents, OpenAI, and n8n workflow automation. Customers can make table reservations through natural voice conversations without phone calls or SMS notifications.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Technologies](#technologies)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

Restaurantia is an AI-powered voice agent specifically designed for restaurant reservation management. Instead of traditional phone calls, customers interact with an intelligent voice assistant that:

- Greets customers warmly and naturally
- Engages in contextual conversations
- Guides reservation process without being pushy
- Collects reservation details (date, time, guests, special requests)
- Saves reservations to Airtable database
- Integrates with n8n for workflow automation and analytics
- Operates seamlessly in English and German

The agent is built on LiveKit's real-time communication platform, uses OpenAI's GPT-4o-mini for language understanding and generation, Whisper for speech recognition, and TTS for voice synthesis. All reservation data is stored in Airtable for persistent storage and management, while n8n handles workflow automation, logging, and custom business processes.

## Features

- **Bilingual Support**: Seamlessly switches between English and German
- **Natural Voice Conversations**: Real-time voice interactions powered by OpenAI GPT-4o-mini
- **Smart Reservation System**: Intelligent booking with 5-character reservation IDs
- **Airtable Database Integration**: Persistent reservation data storage and management
- **n8n Workflow Automation**: Webhook-based logging, analytics, and custom workflows
- **Reservation Management**: Book, update, and retrieve reservations
- **Automatic Call Ending**: Gracefully ends calls after successful bookings
- **Multi-turn Conversations**: Context-aware conversations that follow customer leads
- **Noise Cancellation**: Built-in audio filtering for clearer speech recognition
- **Multilingual Turn Detection**: Automatic language detection during calls
- **Comprehensive Logging**: Full conversation and transaction logging via n8n webhooks

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Customer (Voice Conversation)                │
└─────────────────┬───────────────────────────────────────┘
                  │ (WebSocket)
┌─────────────────▼───────────────────────────────────────┐
│         LiveKit Cloud / Self-Hosted Server             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │  LiveKit Agents Framework                           │ │
│ │  • Whisper STT (Speech-to-Text Recognition)        │ │
│ │  • GPT-4o-mini LLM (Language Model)                │ │
│ │  • OpenAI TTS (Text-to-Speech Synthesis)           │ │
│ │  • Multilingual Turn Detection                      │ │
│ │  • Noise Cancellation (BVC)                         │ │
│ │  • Silero VAD (Voice Activity Detection)            │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────┬──────────────────────────────────────┬────────┘
          │                                      │
          ▼                                      ▼
    ┌──────────────┐                    ┌──────────────┐
    │  Airtable    │                    │  n8n Cloud   │
    │  Database    │◄──────HTTP API─────┤  Workflows   │
    │              │                    │              │
    │ • Bookings   │                    │ • Logging    │
    │ • Analytics  │                    │ • Analytics  │
    │ • History    │                    │ • Custom     │
    │ • Reviews    │                    │   Processing │
    │              │                    │ • Webhooks   │
    └──────────────┘                    └──────────────┘
```

**Data Flow:**

1. **Voice Capture**: Customer speaks to agent via LiveKit connection
2. **Speech Processing**: Agent processes speech with OpenAI:
   - Whisper converts speech to text
   - GPT-4o-mini understands and generates response
   - OpenAI TTS converts response to speech
3. **Reservation Booking**: When booking confirmed:
   - Data saved to Airtable database
   - Webhook triggered to n8n
4. **Data Persistence**:
   - Airtable stores reservation permanently
   - Indexing and history maintained
5. **Workflow Automation**:
   - n8n logs conversation details
   - Processes analytics
   - Triggers custom business workflows
   - Can send notifications or additional processing

## Prerequisites

Before starting, ensure you have:

### Software
- **Python 3.10+**: [Download](https://www.python.org/downloads/)
- **pip/uv**: Python package manager
- **Git**: [Download](https://git-scm.com/)

### Cloud Services & Accounts
- **LiveKit Cloud Account**: [Create](https://cloud.livekit.io/) or [Self-hosted](https://docs.livekit.io/home/self-hosted)
- **OpenAI Account**: [Create](https://platform.openai.com/) with API access and credits
- **Airtable Account**: [Create](https://airtable.com/) for database
- **n8n Instance**: [Cloud](https://n8n.cloud/) or [Self-hosted](https://docs.n8n.io/)

### API Keys & Credentials
- LiveKit API Key and Secret
- OpenAI API Key
- Airtable API Token and Base ID
- n8n webhook URL (provided by n8n after workflow creation)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/restaurantia-voice-agent.git
cd restaurantia-voice-agent
```

### 2. Create Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or with uv (faster):

```bash
uv pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env.local` in project root:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_api_secret_here

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here

# Airtable Configuration
AIRTABLE_API_TOKEN=pat_your_token_here
AIRTABLE_BASE_ID=appYourBaseIdHere
AIRTABLE_TABLE_NAME=Order Summary
```

**Getting Your Credentials:**

#### LiveKit
1. Go to [LiveKit Cloud Console](https://cloud.livekit.io/)
2. Create a new project
3. Click "API Keys" tab
4. Copy Websocket URL, API Key, and API Secret

#### OpenAI
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Navigate to API keys section
3. Create new secret key
4. Copy the key (shown only once)

### Airtable Setup

1. **Create Airtable Base:**
   - Go to [Airtable](https://airtable.com/)
   - Create new base called "Restaurant Reservation"

2. **Create Table:**
   - Name: "Order Summary"
   - Add fields with these exact names:

| Field Name | Type | Description |
|-----------|------|-------------|
| Reservation ID | Single line text | 5-character unique ID |
| Customer Name | Single line text | Customer's full name |
| Reservation Date | Date | Date of reservation |
| Reservation Time | Single line text | Time in HH:MM format |
| Reservation Summary | Long text | Guest count + special requests |

3. **Get Your Credentials:**
   - **Base ID**: Found in URL (`https://airtable.com/BASE_ID/...`)
   - **API Token**: 
     1. Go to [Account Settings](https://airtable.com/account)
     2. Click "Personal Access Tokens"
     3. Create new token with:
        - Scopes: `data.records:read`, `data.records:write`
        - Workspace Access: Your workspace

4. **Add to `.env.local`:**
   ```env
   AIRTABLE_API_TOKEN=pat_your_token_here
   AIRTABLE_BASE_ID=appYourBaseIdHere
   AIRTABLE_TABLE_NAME=Order Summary
   ```

**Reference:** [Airtable API Documentation](https://airtable.com/api)

### 5. Verify Installation

```bash
python src/agent.py --help
```

Should display LiveKit Agents CLI help.

## Configuration

### LiveKit Setup

**Option 1: LiveKit Cloud (Recommended for getting started)**

1. Create account at https://cloud.livekit.io/
2. Create new project (free tier available)
3. Generate API credentials
4. Copy credentials to `.env.local`

**Option 2: Self-Hosted LiveKit**

Follow [LiveKit Self-Hosted Documentation](https://docs.livekit.io/home/self-hosted):

```bash
docker pull livekit/livekit-server
docker run --rm -it -p 7880:7880 \
  -e LIVEKIT_API_KEY=devkey \
  -e LIVEKIT_API_SECRET=secret \
  livekit/livekit-server
```

Then set in `.env.local`:
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

### n8n Workflow Setup

See [n8n Documentation](https://docs.n8n.io/) for detailed setup.

**Create Workflow:**

1. Go to n8n dashboard
2. Click "New workflow"
3. Add Webhook trigger:
   - Method: POST
   - Path: `restaurant-booking`
4. Add processing nodes (optional):
   - Database nodes for logging
   - Notification nodes
   - Custom business logic
5. Add "Respond to Webhook" node at end
6. Activate workflow
7. Copy webhook URL

**Webhook Trigger Configuration:**

```json
{
  "name": "Restaurant Booking Webhook",
  "method": "POST",
  "path": "restaurant-booking",
  "expectedData": {
    "customerName": "string",
    "reservationId": "string",
    "date": "string",
    "time": "string",
    "guests": "number"
  }
}
```

**Expected Payload from Agent:**

```json
{
  "sessionId": "room_name",
  "customerName": "John Doe",
  "customerPhone": "Unknown",
  "reservationId": "A7K2P",
  "date": "2025-10-15",
  "time": "19:00",
  "guests": 4,
  "airtableDate": "10/15/2025",
  "startTime": "2025-10-15T19:00:00",
  "specialRequests": "Birthday dinner",
  "service": "table_booking",
  "airtableStatus": "saved",
  "language": "en"
}
```

## Usage

### Start the Agent

```bash
python src/agent.py start
```

Or with uv:

```bash
uv run src/agent.py start
```

The agent will connect to LiveKit and wait for incoming calls/connections.

### Making a Test Call

**Create a test room and connect:**

```bash
# Using LiveKit CLI
livekit-cli join-room \
  --url ws://localhost:7880 \
  --token <generated-token> \
  --room test-room \
  --name "Test Customer"
```

Or use [LiveKit Playground](https://playground.livekit.io/) for web-based testing.

### Example Conversation Flow

**English:**
```
Agent: "Hi there! Welcome to Restaurantia. How can I help you today?"
Customer: "I'd like to make a reservation"
Agent: "Sure! What's your name?"
Customer: "It's Sarah"
Agent: "Thanks Sarah! When would you like to dine with us?"
Customer: "Tomorrow at 7 PM for 2 people"
Agent: "Perfect! Your reservation is confirmed for Sarah on 10/12/2025 at 19:00 for 2 guests. Your reservation ID is A7K2P. We look forward to seeing you!"
Agent: "Thank you for calling! We look forward to seeing you. Goodbye!"
[Call ends]
```

**German:**
```
Agent: "Hallo! Willkommen bei Restaurantia. Wie kann ich dir heute helfen?"
Customer: "Ich möchte einen Tisch reservieren"
Agent: "Gerne! Wie heißt du?"
Customer: "Ich bin Sarah"
Agent: "Danke Sarah! Wann möchtest du bei uns essen?"
Customer: "Morgen um 19 Uhr für 2 Personen"
Agent: "Perfekt! Deine Reservierung ist bestätigt für Sarah am 12.10.2025 um 19:00 Uhr für 2 Personen. Deine Reservierungs-ID ist A7K2P. Wir freuen uns auf dich!"
Agent: "Danke für deinen Anruf! Wir freuen uns auf dich. Auf Wiedersehen!"
[Anruf endet]
```

### Language Selection

Pass language in room metadata when creating connection:

```json
{
  "customerName": "John Doe",
  "customerPhone": "+49123456789",
  "language": "de"  // "en" for English, "de" for German
}
```

## API Documentation

### RestaurantiaAgent Class

**Constructor:**
```python
RestaurantiaAgent(
    customer_name: str = None,
    customer_phone: str = None,
    language: str = "en",
    session_id: str = "unknown"
)
```

### book_table() Function Tool

Books a table reservation and saves to Airtable.

```python
@function_tool
async def book_table(
    customer_name: str,
    date: str,
    time: str,
    guests: int,
    special_requests: str = ""
)
```

**Parameters:**
- `customer_name` (str, required): Customer's full name
- `date` (str, required): Date in YYYY-MM-DD or M/D/YYYY format
- `time` (str, required): Time in HH:MM 24-hour format (e.g., 19:00)
- `guests` (int, required): Number of guests (1-20)
- `special_requests` (str, optional): Special requests or preferences

**Returns:**
- Confirmation message with 5-character reservation ID

**Example:**
```python
result = await agent.book_table(
    customer_name="John Doe",
    date="2025-10-15",
    time="19:00",
    guests=4,
    special_requests="Birthday dinner, vegetarian options"
)
```

**Response:**
```
"Perfect! Your reservation is confirmed for John Doe on 10/15/2025 at 19:00 for 4 guests. Your reservation ID is A7K2P. We look forward to seeing you!"
```

### update_reservation() Function Tool

Updates an existing reservation.

```python
@function_tool
async def update_reservation(
    reservation_id: str,
    date: str = None,
    time: str = None,
    guests: int = None,
    special_requests: str = None
)
```

**Parameters:**
- `reservation_id` (str, required): 5-character reservation ID
- `date` (str, optional): New date
- `time` (str, optional): New time
- `guests` (int, optional): New guest count
- `special_requests` (str, optional): New special requests

**Returns:**
- Confirmation message

### end_call() Function Tool

Ends the call gracefully after successful booking.

```python
@function_tool
async def end_call()
```

**Returns:**
- Professional goodbye message in appropriate language

## Technologies

### Core Frameworks

| Technology | Purpose | Link |
|-----------|---------|------|
| **LiveKit Agents** | Real-time voice agent framework | [Docs](https://docs.livekit.io/agents/) |
| **OpenAI API** | Language model, STT, TTS | [Docs](https://platform.openai.com/docs) |
| **Airtable API** | Database for reservations | [Docs](https://airtable.com/api) |
| **n8n** | Workflow automation & webhooks | [Docs](https://docs.n8n.io/) |

### Python Libraries

```
aiohttp==3.9.x              # Async HTTP client for webhooks
pyairtable==2.x.x           # Airtable Python SDK
livekit==0.8.x              # LiveKit SDK
livekit-agents==0.8.x       # LiveKit Agents framework
livekit-plugins-openai==0.8.x # OpenAI integration
livekit-plugins-silero==0.8.x # Silero VAD plugin
python-dotenv==1.0.x        # Environment variables
```

### External Services

- **Speech Recognition**: OpenAI Whisper
- **Language Processing**: GPT-4o-mini
- **Text-to-Speech**: OpenAI TTS
- **Database & Storage**: Airtable (persistent reservation data)
- **Real-time Communication**: LiveKit
- **Workflow Automation**: n8n (logging, analytics, webhooks)

### Integration Architecture

```
┌─ Voice Input/Output ─┐
│  OpenAI Whisper      │──► GPT-4o-mini ──► OpenAI TTS
│  (Speech-to-Text)    │    (Language Model)  (Text-to-Speech)
└──────────────────────┘
            │
            ▼
    ┌──────────────┐
    │   Airtable   │◄──── Booking Data (HTTP API)
    │   Database   │      • Store Reservations
    │              │      • Track History
    │              │      • Manage Data
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   n8n Cloud  │     • Logging
    │   Workflows  │     • Analytics
    │              │     • Custom Processing
    │              │     • Integrations
    └──────────────┘
```

## Project Structure

```
restaurantia-voice-agent/
├── src/
│   └── agent.py                 # Main agent implementation
├── .env.example                 # Example environment variables
├── .env.local                   # Local environment variables (gitignored)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── LICENSE                      # MIT License
└── docs/
    ├── setup.md                 # Detailed setup guide
    ├── api.md                   # API reference
    ├── troubleshooting.md       # Common issues and solutions
    └── n8n-workflows.md         # n8n workflow examples
```

## Troubleshooting

### LiveKit Connection Error (401 Unauthorized)

**Error:** `WSServerHandshakeError: 401, message='Invalid response status'`

**Solution:**
1. Verify LiveKit credentials in `.env.local`
2. Check for extra spaces or typos
3. Ensure API key and secret are from correct project
4. Regenerate credentials if needed

### Airtable Field Not Found

**Error:** `UNKNOWN_FIELD_NAME: Unknown field name: "Customer Phone"`

**Solution:**
1. Verify exact field names in Airtable table
2. Field names are case-sensitive and must include spaces
3. Check table name in `.env.local` matches Airtable

### n8n Webhook Not Triggering

**Error:** Booking data not appearing in n8n

**Solution:**
1. Verify n8n workflow is **Active** (toggle enabled)
2. Check webhook URL matches n8n path
3. Ensure **Respond to Webhook** node exists in workflow
4. Check n8n execution logs for errors
5. Test webhook manually:
   ```bash
   curl -X POST "https://your-n8n-url/webhook/restaurant-booking" \
     -H "Content-Type: application/json" \
     -d '{"test":"data"}'
   ```

### Audio Issues

**No speech recognition:**
- Check microphone permissions
- Verify OpenAI STT is configured for correct language
- Test microphone in system settings

**No voice output:**
- Check speaker volume
- Verify OpenAI TTS is enabled
- Check browser/application audio permissions

### Date/Time Parsing Error

**Error:** `Date/time parsing error`

**Solution:**
- Provide date in format: MM/DD/YYYY or YYYY-MM-DD
- Provide time in 24-hour format: HH:MM
- Example: "2025-10-15" at "19:00"

## Security Best Practices

- **Never commit `.env.local`** - Use `.gitignore`
- **Rotate API keys regularly**
- **Use environment variables** for all credentials
- **Enable HTTPS** for n8n webhooks
- **Validate all incoming data** in n8n workflows
- **Use RBAC** for Airtable access
- **Monitor usage** of OpenAI API

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

**Documentation:**
- [LiveKit Agents](https://docs.livekit.io/agents/)
- [OpenAI API](https://platform.openai.com/docs)
- [Airtable API](https://airtable.com/api)
- [n8n Documentation](https://docs.n8n.io/)

**Issues & Questions:**
- GitHub Issues: Create issue with detailed description
- LiveKit Community: https://livekit.io/community
- n8n Community: https://community.n8n.io/

---

**Made with ❤️ by Restaurantia Team**

Last Updated: October 12, 2025
