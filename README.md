# Address Comparison WebApp

A professional Django web application for querying, normalizing, and comparing address data from MongoDB and the CDS API. Features a unified, modern UI for both data sources, field-aligned address comparison, and Loqate filtering.

## Features
- Query and compare addresses from MongoDB and CDS API
- Unified, accessible UI with modern design (Tailwind CSS)
- Field-aligned address comparison for both sources
- Loqate-only filter for standardized addresses
- Modular, OOP codebase with best practices
- Environment-based configuration for security
- Unit tests for CDS client logic

## Requirements
- Python 3.12+
- pip
- MongoDB (local or remote)
- Access to CDS API (for CDS lookups)

## Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/enriquezhandel/addressComparisonWebApp.git
   cd addressComparisonWebApp
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   # Or
   source venv/bin/activate  # On Mac/Linux
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your MongoDB and CDS API credentials.

5. **Run migrations:**
   ```powershell
   python manage.py migrate
   ```

6. **Run the development server:**
   ```powershell
   python manage.py runserver
   ```

7. **Access the app:**
   - Go to [http://127.0.0.1:8000/address-comparison/](http://127.0.0.1:8000/address-comparison/)

## Usage
- Use the sidebar to select MongoDB Query or CDS API Lookup, or use the Unified Lookup to compare both sources.
- Use the Loqate Only filter to restrict results to Loqate-standardized addresses.
- Field-aligned address comparison is shown for each entity.

## Running Tests
```powershell
python manage.py test address_comparison_app
```

## Security & Deployment Notes
- **Never commit secrets or production credentials to the repository.**
- Set `DEBUG = False` and configure `ALLOWED_HOSTS` in `webapp/settings.py` for production.
- Use a secure, unique `SECRET_KEY` in your `.env` file.
- For production, collect static files and use a production-ready server (e.g., Gunicorn, uWSGI).

## CI/CD
- GitHub Actions is set up for automated testing on every push and pull request.

---

**For production deployment, configure your environment variables and static files as needed.**
