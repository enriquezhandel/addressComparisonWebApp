# Address Comparison WebApp

A professional Django web application for querying, normalizing, and comparing address data from MongoDB.

## Requirements
- Python 3.12+
- pip
- MongoDB (local or remote)

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
   - Copy `.env.example` to `.env` and fill in your MongoDB credentials, or edit `.env` directly.

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

## Running Tests
```powershell
python manage.py test address_comparison_app
```

## CI/CD
- GitHub Actions is set up for automated testing on every push and pull request.

---

**For production deployment, configure your environment variables and static files as needed.**
