# Edible Gift Finder

AI-powered product discovery for [Edible Arrangements](https://www.ediblearrangements.com). Helps customers find the right gift through conversational recommendations, product comparisons, and guided search.

## Features

- **Gift recommendations** — Get personalized suggestions based on occasion, budget, and recipient
- **Refinement** — Iterate on results with feedback like "cheaper," "more fun," or "something different"
- **Product comparison** — Compare 2–3 products side-by-side (price, occasion, ingredients, best use case)
- **Clarifying questions** — Handles vague queries by asking about occasion and budget
- **Popular products shelf** — Featured products on load to help users get started

## Tech Stack

- **Backend:** Flask, Python 3.10+
- **LLM:** OpenAI GPT-4o-mini (via Responses API)
- **Catalog:** [Edible Arrangements Search API](https://www.ediblearrangements.com/api/search/)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/JimmyWu-Peiyuan/edible-gift-finder.git
cd edible-gift-finder
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

Copy the example env file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and set:

```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run

```bash
python -m flask --app flask_app run --port 5000
```

Or use the convenience script:

```bash
./run_flask.sh
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project Structure

```
├── app/
│   ├── prompts/          # LLM prompts (intent, recommender, comparison, followup)
│   └── service/         # Intent classifier, orchestrator, recommender, comparison
├── templates/           # Chat UI
├── static/              # Logo and assets
├── data/                # Popular products cache
├── flask_app.py         # API routes
└── requirements.txt
```

## Architecture

- **Layer 1 — Intent classifier:** Classifies user messages (greeting, search, refinement, compare, vague)
- **Layer 2 — Orchestrator:** Routes to follow-up questions, recommendations, or comparison
- **Hallucination guards:** LLM outputs are validated against the catalog; only exact matches are shown

## License

MIT
