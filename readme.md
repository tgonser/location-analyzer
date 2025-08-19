# 🗺️ Location Analyzer

A powerful, modern tool for analyzing Google Location History data with real-time web interface and detailed travel analytics.

![Location Analyzer Demo](https://via.placeholder.com/800x400/007bff/ffffff?text=Location+Analyzer+Real-time+Dashboard)

## ✨ Features

- **🌐 Beautiful Web Interface** - Modern, responsive design with real-time feedback
- **📊 Real-time Progress Tracking** - Watch your analysis happen live with progress bars and status updates
- **🏙️ City & Country Detection** - Automatically identifies all locations visited
- **⏱️ Time Tracking** - Calculates time spent in each location
- **🚀 Location Jumps Analysis** - Tracks significant movements between cities
- **📈 Distance Calculation** - Computes total travel distance
- **📁 Multiple Export Formats** - CSV files and detailed summary reports
- **🖥️ Dual Interface** - Both web application and desktop GUI
- **⚡ High Performance** - Modern async processing for large datasets
- **🔒 Privacy Focused** - All processing happens locally on your machine

## 🎥 Demo

**Real-time Analysis in Action:**
- Upload your Google Location History file
- Watch live progress updates as data is processed
- See statistics appear in real-time
- Download detailed CSV reports instantly

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Geoapify API key (free at [geoapify.com](https://www.geoapify.com))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/location-analyzer.git
   cd location-analyzer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your API key:**
   - Visit [geoapify.com](https://www.geoapify.com)
   - Sign up for a free account
   - Copy your API key

4. **Export Google Location History:**
   - Go to [Google Takeout](https://takeout.google.com)
   - Select "Location History (Timeline)"
   - Choose JSON format
   - Download and extract the Records.json file

### Usage

**Web Interface (Recommended):**
```bash
python app.py
```
Then open: http://localhost:5000

**Desktop GUI:**
```bash
python gui_app.py
```

## 📊 Output Files

- **`city_jumps.csv`** - Movement between cities with distances and timing
- **`by_city_location_days.csv`** - Time spent in each city
- **`by_state_location_days.csv`** - Time spent in each state/country
- **`analysis_summary.txt`** - Overview with top destinations

## 🏗️ Architecture

- **Modern Async Engine** - Efficient API processing with async/await
- **Intelligent Caching** - Reduces API calls and speeds up repeated analysis
- **Real-time Updates** - Background processing with live progress feedback
- **Clean Code Structure** - Well-organized, maintainable codebase

## 🔧 Configuration

Create `config/web_config.json`:
```json
{
  "geoapify_key": "your_api_key_here",
  "last_start_date": "2024-01-01",
  "last_end_date": "2024-12-31"
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Google for Location History data export
- Geoapify for geocoding services
- Flask for the web framework
- The Python community for excellent libraries

---

**🎉 Happy analyzing! Discover your travel patterns with beautiful real-time feedback.**