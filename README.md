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

## Installation
### Clone the repository:
 - git clone https://github.com/katamveerakowshik/statustracker.git
 - cd statuspage_project

### Create and activate a virtual environment:
 - python -m venv venv
 - venv\Scripts\activate
   
### Install dependencies:
 - pip install -r requirements.txt

### Apply migrations:
 - python manage.py migrate

### Run the development server:
 - python manage.py runserver

## Checkout the deployed application here: 
https://statustracker-1.onrender.com/
