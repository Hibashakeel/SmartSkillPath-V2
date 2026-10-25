# SmartSkillPath — Career Discovery Website

This website wraps the existing SmartSkillPath recommendation model in a redesigned, multi-page React experience. The original Streamlit application, model and datasets are retained in `Backend/`.

## Website experience
- Separate Home, About, Explore, Certifications and My Space pages in the top navigation.
- Dark navy visual identity with blue/purple gradients, subtle animation, responsive layouts and custom illustrations built from CSS/UI components.
- Guest users can use the existing model from Explore: choose a career, select current skills and view temporary recommendations. Guest results and selections are not saved.
- The Certifications page links to official providers and shows general free/paid guidance. Fees and availability can change; users should confirm details on the provider's official page.
- Sign-in/register is provided for account-only features. The backend now supports persisted goals, saved recommendations, ordered roadmap items, roadmap progress, and logout/token revocation. The current My Space frontend is still a placeholder and is not connected to these persistence endpoints.
- The original Streamlit app remains available as `Backend/app.py`.

## Requirements
- Python 3.10+ recommended
- Node.js 20+ recommended

## Run the website on Windows
Use two terminals from the project root.

### 1. Start the backend API
```bat
cd Backend
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements-web.txt
py -m uvicorn api_server:app --reload --host 127.0.0.1 --port 8000
```
If your system uses `python` rather than `py`, replace `py` with `python`.
The API applies repeatable, additive SQLite table/index creation at startup. To test against a separate database instead of `Backend/smartskillpath_users.db`, set `SMARTSKILLPATH_DB` to a temporary database path before starting Uvicorn.

### Run backend persistence tests
From the project root:
```bat
cd Backend
py -m unittest discover -s tests -v
```
The test suite uses temporary databases and does not migrate the project database.

### 2. Start the frontend
Open a second terminal:
```bat
cd Frontend
npm install
npm run dev
```
Open the local URL printed by Vite, normally `http://localhost:5173`.

## Run the original Streamlit app
```bat
cd Backend
py -m pip install -r requirements-web.txt
py -m streamlit run app.py
```

## Notes
- Keep `Backend/outputs/cleaned_data/` and the original model/data files in place.
- The first model request can take longer while the model loads/processes data.
- This is a local development/demo starter, not yet a production deployment. Before a public launch, connect the My Space frontend to the persistence API and implement secure session handling, HTTPS, rate limiting, email verification/password reset and a privacy policy.
- Certification cost labels are indicative, not a live price feed.
