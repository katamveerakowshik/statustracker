# statustracker
# Status Page Application

A full-stack status page application built with Django and Bootstrap that allows organizations to manage and publish the real-time status of their services.

## Features

- **User Authentication**: Secure registration, login, and logout using Django Allauth
- **Multi-Tenant Support**: Separate organizations with isolated data
- **Service Management**: Track status of multiple services with color-coded indicators
- **Incident Management**: Create, update, and resolve incidents or scheduled maintenances
- **Real-time Updates**: WebSocket-based real-time status updates to all connected clients
- **Public Status Page**: Shareable public status page for each organization

## Tech Stack

- **Frontend**: Bootstrap 5, JavaScript, WebSockets
- **Backend**: Django 4.x, Django REST Framework, Django Channels
- **Database**: PostgreSQL (or SQLite for local development)
- **Authentication**: Django Allauth

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- PostgreSQL (optional, can use SQLite for development)

Installation
Clone the repository:

bash
git clone https://github.com/yourusername/statuspage-app.git
cd statuspage-app
Create and activate a virtual environment:

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

bash
pip install -r requirements.txt
Configure environment variables:

Copy .env.example to .env and fill in your settings.

Apply migrations:

bash
python manage.py migrate
Create a superuser:

bash
python manage.py createsuperuser
Run the development server:

bash
python manage.py runserver

### Checkout the deployed application here: 
https://statustracker-1.onrender.com/
