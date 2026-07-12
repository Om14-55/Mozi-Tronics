# Factory Production Monitoring & Data Simulation System

A complete industrial production monitoring system that simulates machine data, stores it in a MySQL database, and visualizes production metrics through a Django-based web dashboard.

## Project Overview

This project provides an end-to-end solution for monitoring factory production lines. It includes:

* Machine data simulator
* Django REST API backend
* MySQL database
* Production analytics dashboard
* Client-Factory-Line based monitoring
* Production logs and graphical reports

The system is designed to simulate real-time production data from industrial machines and display it on an interactive web dashboard.

---

## Project Structure

```text
final_sql_webapp_dump_final_version_3.2/
│
├── Dump20260707.sql                     # MySQL database dump
├── installation_instruction.txt         # Installation guide
│
├── machine_simulator_singleV2_latest/   # Machine data simulator
│
├── web_appV2/                           # Django web application
│
└── README.md
```

---

## Features

* Real-time production monitoring
* Machine data simulation
* MySQL database integration
* Django REST APIs
* Dashboard analytics
* Production graphs
* Client & Factory management
* Line-wise production reports
* User Authentication
* Historical production records

---

## Tech Stack

### Backend

* Python
* Django
* Django REST Framework

### Database

* MySQL

### Frontend

* HTML
* CSS
* JavaScript

### Other Tools

* Gunicorn
* Nginx
* Python Socket Programming

---

## Modules

### Machine Simulator

Simulates production machine data and continuously sends production information to the server.

### Django Backend

Provides REST APIs for:

* Login
* User Registration
* Production Data
* Dashboard Graphs
* Client Management
* Factory Management
* Line Management

### Dashboard

Displays:

* Production Statistics
* Efficiency
* Downtime
* Rejections
* Cases Packed
* Graphical Reports
* Latest Production Logs

---

## Database

The project includes a complete MySQL database dump:

```
Dump20260707.sql
```

Import this file before running the application.

---

## Installation

1. Clone the repository.

```bash
git clone <repository-url>
```

2. Import the MySQL database.

3. Create a Python virtual environment.

```bash
python -m venv venv
```

4. Activate the environment.

```bash
source venv/bin/activate
```

or (Windows)

```bash
venv\Scripts\activate
```

5. Install dependencies.

```bash
pip install -r requirements.txt
```

6. Configure database settings.

7. Run migrations if required.

```bash
python manage.py migrate
```

8. Start the Django server.

```bash
python manage.py runserver
```

9. Start the machine simulator.

---

## Requirements

* Python 3.x
* MySQL
* Django
* Django REST Framework
* Gunicorn (Production)
* Nginx (Production)

---

## Use Cases

* Factory Production Monitoring
* Industrial Machine Simulation
* Manufacturing Analytics
* Production Dashboard
* Production Data Collection
* Factory Management

---

## Future Improvements

* Live WebSocket updates
* Email notifications
* Machine health monitoring
* Predictive maintenance
* AI-based production analytics
* Export reports (PDF/Excel)

---

## Author

**Rohit Shaw**

Software Engineer | Python Developer | Django Developer | AI & Machine Learning Enthusiast

---

## License

This project is intended for educational and industrial demonstration purposes.
