# HDT AI Agent (FastAPI)

This service implements AI chatbot conversation endpoints.

From your screenshot ("AI Agent Actions"), these gateway paths are implemented:

- `POST /models/chatbot` (send message to chatbot)
- `GET /models/chatbot` (list conversations / responses)

Additional implemented endpoint:

- `GET /models/chatbot/{conversation_id}` (get one conversation)
- `DELETE /models/chatbot/{conversation_id}` (delete one conversation)

These routes are exposed through `HDT-API-Gateway` via `/models/chatbot`.

## Run

1. Install dependencies
   - `pip install -r requirements.txt`
2. Start the server
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Endpoints

### Send message

`POST /models/chatbot`

Body (JSON):
```json
{
  "message": "Hello AI",
  "conversation_id": null
}
```

### Retrieve conversations

`GET /models/chatbot?limit=50&offset=0`

### Retrieve one conversation

`GET /models/chatbot/{conversation_id}`

### Delete conversation

`DELETE /models/chatbot/{conversation_id}`

