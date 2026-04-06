# Goodreads Scraper

A lightweight Flask application for searching and scraping book data from Goodreads. It provides a simple search interface and an API endpoint that returns book titles, authors, ratings, and high-resolution cover images.

## Features
- Results are cached in memory for 5 minutes to improve response times for repeat searches.
- Automatically converts small search thumbnails into high-quality 600x900 book covers.
- Asynchronous frontend using JavaScript Fetch API for a smooth search experience.
- Pre-configured for deployment on Vercel with no additional setup needed.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```
3. Open http://localhost:5000 in your browser.

## Project Structure
- app.py: The main Flask server containing the scraping logic and cache management.
- static/: Contains the style.css and app.js files for the frontend.
- templates/: Contains index.html, the main user interface.
- requirements.txt: List of Python dependencies (Flask, Requests, BeautifulSoup4).

## Deployment
This project is structured for easy deployment to Vercel. To deploy, push the files to a GitHub repository and import it into Vercel. Vercel will automatically detect the Python environment and handle the build process.
