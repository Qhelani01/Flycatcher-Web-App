# 🦅 Flycatcher Web App

A modern, responsive web application for exploring bird observations in Southern Africa, built with Python Flask and powered by real-time eBird data.

## ✨ Features

- **🌍 Interactive Map**: Visualize bird observations on Google Maps with custom markers
- **📊 Real-time Data**: Fetch live bird observation data from eBird API
- **🔍 Bird Information**: Learn more about each species with family and order details
- **📱 Responsive Design**: Beautiful, modern interface that works on all devices
- **🎨 Minimalistic Theme**: Clean, monochrome design for optimal user experience
- **🚀 Demo Mode**: Experience the app with one-time data loading for demo purposes

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **APIs**: 
  - [eBird API](https://ebird.org) for bird observation data
  - [Google Maps API](https://developers.google.com/maps) for interactive mapping
- **Styling**: Custom CSS with modern design principles

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Qhelani01/Flycatcher-Web-App.git
   cd Flycatcher-Web-App
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   
   **For Local Development:**
   - Create a `backend/api_keys.py` file with your API keys:
   ```python
   EBIRD_API_KEY = "your_ebird_api_key_here"
   GOOGLE_MAPS_API_KEY = "your_google_maps_api_key_here"
   ```
   
   **For Production (Render):**
   - Set these as environment variables in your hosting platform:
   ```
   EBIRD_API_KEY = your_ebird_api_key_here
   GOOGLE_MAPS_API_KEY = your_google_maps_api_key_here
   DEFAULT_REGION = ZA
   ```
   
   **⚠️ IMPORTANT:** Never commit API keys to GitHub! The `api_keys.py` file is already in `.gitignore`.

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   - Navigate to `http://localhost:8000`
   - Enjoy exploring bird observations!

## 📱 How to Use

1. **Landing Page**: Start at the beautiful landing page with app information
2. **Load Data**: Click "Load Demo Data" to fetch bird observations
3. **Explore Map**: View bird locations on the interactive map
4. **Learn More**: Click "Learn More" on any bird to see species information
5. **Browse List**: View all observations in a clean, organized list

## 🌍 Data Coverage

- **Region**: Southern Africa (primarily South Africa)
- **Data Source**: eBird API with real-time observation data
- **Species Information**: Family and order classification for each bird

## 🎨 Design Features

- **Monochrome Color Palette**: Clean, professional appearance
- **Responsive Layout**: Optimized for desktop, tablet, and mobile
- **Modern UI Elements**: Smooth animations and intuitive navigation
- **Accessibility**: High contrast and readable typography

## 🔧 API Configuration

### eBird API
- Get your API key from [eBird](https://ebird.org)
- Used for fetching bird observation data and species taxonomy

### Google Maps API
- Get your API key from [Google Cloud Console](https://console.cloud.google.com/)
- Used for interactive map visualization

## 📁 Project Structure

```
Flycatcher-Web-App/
├── backend/
│   ├── app.py              # Flask server and API endpoints
│   ├── requirements.txt    # Python dependencies
│   └── api_keys.py        # API key configuration (not in git)
├── frontend/
│   ├── landing.html       # Landing page with app introduction
│   ├── app.html          # Main bird observation application
│   ├── image.png         # App logo
│   └── GOPR0809-Enhanced-NR.jpg  # Developer profile image
└── README.md             # This file
```

## 🤝 Contributing

This is a personal project showcasing modern web development with Python and real-time API integration. Feel free to explore the code and learn from the implementation!

## 📄 License

© Qhelani Moyo 2025. All rights reserved.

## 🙏 Acknowledgments

- **eBird**: For providing comprehensive bird observation data
- **Google Maps**: For powerful mapping capabilities
- **Flask**: For the robust Python web framework

---

**Built with ❤️ for wildlife conservation and technology education**
