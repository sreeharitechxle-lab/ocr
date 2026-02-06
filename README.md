# OCR Scanner Web Application

A Flask-based web application for extracting and managing business card information using OCR technology.

## Features

- Upload and process business card images
- Extract text using OCR (Tesseract)
- Store extracted data in MongoDB
- View, edit, and delete business card records
- Export data to Excel format

## Tech Stack

- **Backend**: Flask, Python 3.11
- **Database**: MongoDB
- **OCR**: Tesseract
- **Frontend**: HTML, CSS, Bootstrap
- **Deployment**: Docker, Render

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/sreeharitechxle-lab/ocr.git
cd ocr
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file
MONGO_URI=mongodb://localhost:27017/business_card_db
```

5. Run the application:
```bash
python app.py
```

### Docker Deployment

1. Build the image:
```bash
docker build -t ocr-scanner .
```

2. Run the container:
```bash
docker run -p 5000:5000 ocr-scanner
```

## Render Deployment Guide

### Prerequisites
- Render account
- MongoDB Atlas cluster
- GitHub repository

### Step-by-Step Deployment

1. **Connect GitHub Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select the `ocr` repository

2. **Configure Service**
   - **Name**: `ocr-scanner`
   - **Environment**: `Docker`
   - **Region**: Choose nearest region
   - **Branch**: `main`

3. **Set Environment Variables**
   ```
   PORT=10000
   PYTHONUNBUFFERED=True
   MONGO_URI=mongodb+srv://your_username:your_password@cluster.mongodb.net/business_card_db?retryWrites=true&w=majority
   ```

4. **Advanced Settings**
   - **Health Check Path**: `/`
   - **Auto-Deploy**: Enabled (pushes to main branch trigger redeploy)

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete (2-5 minutes)
   - Access your app at: `https://ocr-scanner.onrender.com`

### Environment Variables Setup

**Required Variables:**
- `MONGO_URI`: MongoDB connection string
- `PORT`: Render-provided port (default: 10000)
- `PYTHONUNBUFFERED`: Set to `True` for better logging

**Optional Variables:**
- `COMPRESTO_API_KEY`: For image compression (if using Compresto API)

### MongoDB Setup

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a free cluster
3. Create database user with password
4. Add your IP to whitelist (or use 0.0.0.0/0 for Render)
5. Get connection string and update in Render

### Troubleshooting

**Common Issues:**

1. **Build Fails**
   - Check Dockerfile syntax
   - Verify requirements.txt format
   - Check Render build logs

2. **Database Connection Error**
   - Verify MONGO_URI format
   - Check MongoDB Atlas IP whitelist
   - Ensure database user has correct permissions

3. **App Not Loading**
   - Check health check path
   - Verify PORT environment variable
   - Review application logs

**Useful Commands:**
```bash
# Check Render logs
render logs

# Local testing with Docker
docker build -t ocr-scanner .
docker run -p 10000:10000 -e MONGO_URI="your_mongo_uri" ocr-scanner
```

## Project Structure

```
ocr/
├── app.py                 # Main Flask application
├── extraction.py          # OCR and text processing
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── render.yaml           # Render deployment config
├── static/               # CSS and images
├── templates/            # HTML templates
└── uploads/              # File upload directory
```

## API Endpoints

- `GET /` - Home page
- `POST /upload` - Upload and process image
- `GET /view_data` - View all records
- `POST /edit/<id>` - Update record
- `GET /delete/<id>` - Delete record
- `GET /export` - Export to Excel

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
