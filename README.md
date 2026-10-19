🌱 SoilSense - AI-Powered Soil Analysis

SoilSense is a Django-based web application that uses Google's Gemini AI to analyze soil photographs and provide preliminary soil assessments, visible characteristics, possible uses, and recommended laboratory tests.

Features
AI-powered soil image analysis using Google Gemini.
Soil type estimation and visual characteristic assessment.
Soil sample location capture using browser geolocation.
Interactive geographical maps using Plotly.
User registration, login, and authentication.
Soil analysis results stored in a database.
Tech Stack
Backend: Python, Django
AI: Google Gemini API
Database: SQLite
Visualization: Plotly, Pandas
Frontend: HTML, CSS, JavaScript
Image Processing: Pillow
Installation
git clone https://github.com/DishaDandawate/SoilSense.git
cd SoilSense
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt


Create a .env file in the project root:

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
DJANGO_SECRET_KEY=your_django_secret_key
DEBUG=True


Ensure .env is listed in .gitignore.

Run database migrations and start the server:

python manage.py migrate
python manage.py runserver


Open http://127.0.0.1:8000/ in your browser.

Note

SoilSense provides preliminary visual assessments only. Laboratory testing is required for reliable measurements of soil pH, nutrients, and contamination.

License

No license has been specified yet.
