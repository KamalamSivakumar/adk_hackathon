## How to Run the Task Gamifier App

This app integrates a Google ADK-powered task agent with a Flask-based Calendar API. Follow these steps to run the complete workflow.

---

### 1. Start the Calendar API Server

The `calendar_api.py` script is a Flask application that schedules meetings or events via the Google Calendar API.

- Ensure `credentials.json` is present in the **same directory** as `calendar_api.py`.
- In one terminal, from the project root:

```bash
python calendar_api.py
```

This starts the Flask server on `http://localhost:5000`.

---

### 2. Launch the Streamlit + ADK Agent Interface

In a **new terminal**, with the current working directory set to `adk_hackathon`, run the Streamlit UI:

```bash
streamlit run personaliser_adk/app.py
```

This launches the agent interface that lets you input tasks, decompose them, estimate XP, and optionally schedule them on your calendar.

---

### 3. Project Folder Structure

Ensure the following structure is in place:

```
adk_hackathon/
│
├── calendar_api.py
├── credentials.json             # Google Calendar OAuth credentials
│
└── personaliser_adk/
    ├── __init__.py
    ├── agent.py                 # Defines your ADK agent and tools
    ├── app.py                   # Streamlit UI
    └── .env                     # Contains GOOGLE_API_KEY
```

---

### 4. Environment Variables

Inside `personaliser_adk/.env`, add your API key:

```env
GOOGLE_API_KEY=your-google-api-key-here
```

This is required for using the Gemini or Google LLM APIs within the ADK framework.

---

Have fun trying this out, do let me know your feedback!