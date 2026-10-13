# 🌾 CropShield

**CropShield** is an agricultural monitoring and early-warning system designed to help farmers identify potentially harmful heat conditions for their crops.

The system uses real-time weather data and farm-specific temperature thresholds to monitor crop conditions and generate alerts when temperatures become critical.

## 🚀 Technologies Used

### Backend
- **Python** - Core programming language
- **Flask** - Web application framework
- **SQLite** - Database management
- **Twilio API** - SMS alert notifications

### Frontend
- **HTML5** - Web page structure
- **CSS3** - Styling and responsive interface
- **JavaScript** - Client-side interactions and dynamic functionality

### APIs & Services
- **Open-Meteo API** - Real-time weather data
- **Twilio API** - Automated SMS notifications

### Security
- Password hashing for secure user authentication
- Session-based authentication
- Parameterized SQL queries
- Environment variables for sensitive API credentials

## ⚙️ How It Works

CropShield collects farm details such as location, crop, growth stage, and temperature threshold. Weather data is retrieved through the Open-Meteo API and evaluated against the configured threshold.

When the temperature reaches a critical level, the system records the event and can send an SMS alert through Twilio.

## 🎯 Objective

The main objective of CropShield is to reduce the need for continuous manual weather monitoring and provide farmers with **timely, automated heat-risk alerts**.

## 🔮 Future Scope

- Crop-specific risk analysis
- Weather forecast-based alerts
- Humidity and rainfall-based risk assessment
- IoT sensor integration
- Soil moisture monitoring
- Machine-learning-based crop stress prediction
- Cloud deployment and scalable infrastructure

## 📌 Project Status

**Status:** Working Prototype

Developed as a **B.Tech / Hackathon Project** focused on applying software technologies to agricultural monitoring and early-warning systems.
