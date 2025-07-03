## Flight Price Prediction & Search Engine

A comprehensive flight search and price prediction application that scrapes multiple travel websites and uses machine learning to predict flight prices.
![Home](https://github.com/user-attachments/assets/28a767b4-caaf-432a-b3be-aa50e717a451)
![Results](https://github.com/user-attachments/assets/e716a677-1f93-43af-8bdc-e88401c5fe54)
![Predictions](https://github.com/user-attachments/assets/63635353-b0d0-4a66-a178-26278779f401)
## Features

- **Multi-source Flight Search**: Scrapes Royal Air Maroc, TravelWings, and Aviasales
- **AI Price Prediction**: Machine learning models predict flight prices for different routes
- **Price Trend Analysis**: Shows price trends over time
- **Popular Destinations**: AI-powered recommendations based on historical data
- **Localized Predictions**: Location-based price predictions
- **Real-time Search**: Asynchronous flight search with progress tracking

## Tech Stack

- **Backend**: Python Flask
- **Web Scraping**: Selenium with undetected-chromedriver
- **Database**: MongoDB
- **Machine Learning**: Scikit-learn (Random Forest)
- **Frontend**: HTML, CSS, JavaScript
- **Data Processing**: Pandas, NumPy

## Installation

### Prerequisites

- Python 3.8+
- MongoDB
- Chrome browser (for web scraping)

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd projet-data-science
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB**
   - Install MongoDB locally or use MongoDB Atlas
   - Create a database named `flight_database`
   - The application will automatically create the required collections

4. **Initialize the ML models**
   - The application will automatically train models when first run
   - Models are saved in the `models/` folder (excluded from git)
   - You can also trigger model training via the API endpoint `/api/train-model`

## Usage

### Running the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### API Endpoints

- `POST /search` - Initiate a flight search
- `GET /check_status/<search_id>` - Check search progress
- `GET /results/<search_id>` - View search results
- `POST /api/predict-price` - Get price predictions
- `POST /api/train-model` - Retrain ML models
- `GET /api/price-history` - Get recent flight price history

## Project Structure

```
projet-data-science/
├── app.py                 # Main Flask application
├── models/               # ML models (auto-generated, not in git)
├── templates/            # HTML templates
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Machine Learning Models

The application uses route-specific Random Forest models for price prediction:

- Models are automatically trained when the application starts
- Each route (e.g., CDG-JFK) gets its own model
- Models are saved as `.pkl` files in the `models/` folder
- The `models/` folder is excluded from git (see `.gitignore`)

### Model Training

Models are trained automatically using:
- Historical flight data from MongoDB
- Features: airline, stops, days to departure
- Target: flight price in MAD

### Retraining Models

To retrain models with new data:
```bash
curl -X POST http://localhost:5000/api/train-model
```

## Configuration

### Environment Variables

Create a `.env` file for configuration:
```env
MONGODB_URI=mongodb://localhost:27017/
FLASK_SECRET_KEY=your-secret-key
```

### Airport Data

Airport information is stored in the `AIRPORT_DATA` dictionary in `app.py`. You can add new airports by updating this dictionary.

## Deployment

### Local Development
```bash
python app.py
```

### Production
- Use a production WSGI server like Gunicorn
- Set up proper MongoDB authentication
- Configure environment variables
- Use a reverse proxy (nginx)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license here]

## Notes

- The `models/` folder contains trained ML models and is excluded from version control
- Models are automatically generated when the application runs
- Screenshots of errors are saved locally for debugging
- The application uses undetected-chromedriver to avoid detection by travel websites 
