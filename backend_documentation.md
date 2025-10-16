LangApp Backend Documentation
API Overview

Built with Django and Django REST Framework (DRF).
Hosted on AWS Elastic Beanstalk/EC2.
Database: PostgreSQL (AWS RDS).

Authentication

Uses JWT for authorization.
Endpoints:
POST /api/auth/register/: Register user (email, password).
POST /api/auth/login/: Login (email, password) → returns JWT.

Endpoints

POST /api/dictionaries/: Create dictionary (requires JWT, fields: source_lang, target_lang, words[] with translations, images).
GET /api/dictionaries/: List user dictionaries (requires JWT).
GET /api/dictionaries/{id}/: Dictionary details (name, description, languages for public preview).
POST /api/dictionaries/{id}/buy/: Buy dictionary (requires JWT, payment via Stripe).
GET /api/marketplace/: Search dictionaries by themes/languages.

Data Model

User: email, password (hashed).
Dictionary: owner (FK to User), name, description, source_lang, target_lang, price (min $0.50), is_private.
Word: dictionary (FK to Dictionary), text, translation, image_url.

Payments

Integrated with Stripe (or Tinkoff for RF).
30% commission on withdrawals (min $50).

Image Storage

Stored on AWS S3.
Images uploaded via API, also sourced from Unsplash/Pixabay.

Translation Hints

Provided via Google Translate API.

Integration Notes

Send JWT in Authorization: Bearer <token> header for protected endpoints.
