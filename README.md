# sales-backend

## Overview

Welcome to the **sales-backend** project! This backend is built using Django and Django REST Framework to provide robust API endpoints for the sales application.

This document will guide you through the installation and setup process to get the project running on your local machine.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create a Virtual Environment](#2-create-a-virtual-environment)
  - [3. Activate the Virtual Environment](#3-activate-the-virtual-environment)
  - [4. Install Dependencies](#4-install-dependencies)
  - [5. Configure Environment Variables](#5-configure-environment-variables)
  - [6. Apply Migrations](#6-apply-migrations)
  - [7. Create a Superuser](#7-create-a-superuser)
  - [8. Run the Development Server](#8-run-the-development-server)
- [API Endpoints](#api-endpoints)
- [Notes](#notes)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8** or higher
- **pip** (Python package manager)
- **virtualenv** (optional but recommended)
- **Git**

## Installation Steps

### 1. Clone the Repository

Clone the project repository from GitHub to your local machine:

```bash
git clone https://github.com/Hrishi-MiM/sales-backend.git
cd sales-backend
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to manage project dependencies separately from your global Python installation.

#### Using `venv`

```bash
python3 -m venv env
```

### 3. Activate the Virtual Environment

Activate the virtual environment to ensure that all packages are installed locally within it.

- **On macOS and Linux:**

  ```bash
  source env/bin/activate
  ```

- **On Windows:**

  ```bash
  env\Scripts\activate
  ```

### 4. Install Dependencies

Install all the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file is not provided, install the dependencies manually:

```bash
pip install django djangorestframework
```

Then, create the `requirements.txt` file:

```bash
pip freeze > requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project's root directory to store environment-specific settings (optional but recommended for security):

```bash
touch .env
```

Add necessary environment variables, for example:

```env
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Ensure your `settings.py` is configured to read from the `.env` file (you may need to install `python-decouple` or similar packages).

### 6. Apply Migrations

Apply the database migrations to set up the initial database schema:

```bash
python manage.py migrate
```

### 7. Create a Superuser

Create an administrative user to access the Django admin interface:

```bash
python manage.py createsuperuser
```

Provide a username, email, and password when prompted.

### 8. Run the Development Server

Start the Django development server to run the application locally:

```bash
python manage.py runserver
```

Access the application at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## API Endpoints

The **sales-backend** provides various API endpoints for managing sales data. Below are some of the primary endpoints:

- **Order API:** `/api/orders/`
- **Product API:** `/api/products/`
- **Customer API:** `/api/customers/`

Refer to the API documentation or codebase for detailed information on request and response formats.

## Notes

- **Virtual Environment Activation:** Remember to activate your virtual environment each time you work on the project.
- **Installing New Packages:** If you install new packages, update the `requirements.txt` file:

  ```bash
  pip freeze > requirements.txt
  ```

- **Database Configuration:** The project is configured to use SQLite by default. To use another database (e.g., PostgreSQL), update the `DATABASES` setting in `settings.py` accordingly.
- **Static Files:** For serving static files in development, ensure `STATIC_URL` and `STATICFILES_DIRS` are correctly set in `settings.py`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

You're all set! If you encounter any issues during installation, please refer to the Django documentation or contact the project maintainers for assistance.

Happy coding!