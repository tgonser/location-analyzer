# Location Analyzer - Claude Code Configuration

## Project Overview

A powerful, modern web-based tool for analyzing Google Location History data with real-time interface and detailed travel analytics. **Originally started as a desktop application but has evolved into a full web application.** This project processes Google Location History JSON files (from the new mobile exporter, not Google Takeout) to generate insights about travel patterns, time spent in locations, and movement analysis.

## Tech Stack

- **Backend**: Python 3.8+ with Flask web framework
- **Frontend**: Modern responsive web interface with real-time updates
- **APIs**: Geoapify for geocoding services with intelligent caching
- **Data Processing**: Async processing for large datasets with noise filtering
- **Export Formats**: CSV files and detailed summary reports

## Architecture & Key Features

- 🌐 **Primary Web Interface** with real-time feedback (desktop GUI deprecated)
- 📊 **Critical Progress Tracking** - keeping users informed during file processing
- 🏙️ City & Country Detection via geocoding APIs with caching layer
- ⏱️ Time Tracking calculations for location analysis
- 🚀 Location Jumps Analysis for movement tracking
- 📈 Distance Calculation for travel metrics
- 📁 Multiple Export Formats (CSV + summary reports)
- ⚙️ **User-Configurable Settings** for optimized output analysis
- ⚡ **Noise-Filtered Data Processing** - uses pre-processed JSON files
- 🔒 Privacy Focused - all local processing

## Development Setup

### Prerequisites

- Python 3.8+
- Geoapify API key (free at geoapify.com)
- **Google Location History data from NEW mobile exporter** (NOT Google Takeout)
- **Pre-processed JSON file** (cleaned of noise using companion preprocessing app)

### Installation Commands

```bash
# Clone and setup
git clone https://github.com/tgonser/location-analyzer.git
cd location-analyzer
pip install -r requirements.txt

# Create configuration
mkdir -p config
# Add your API key to config/web_config.json
```

### Configuration Files

**config/web_config.json** (required):

```json
{
  "geoapify_key": "your_api_key_here",
  "last_start_date": "2024-01-01", 
  "last_end_date": "2024-12-31"
}
```

## Running the Application

### Web Interface (Primary Interface)

```bash
python app.py
# Open: http://localhost:5000
```

### Legacy Desktop GUI (Deprecated)

```bash
python gui_app.py
# Note: Focus is now on web interface
```

## Data Pipeline & Workflow

### Input Data Requirements

- **Google Location History from NEW mobile exporter** (not Google Takeout)
- **CRITICAL**: Must use pre-processed JSON file, not raw Google export
- Raw Google JSON contains significant noise in data points
- **Companion preprocessing app** cleans and streamlines the data for analysis

### Data Processing Architecture

1. **Raw Google JSON** → **Preprocessing App** → **Clean JSON for analysis**
1. Upload clean JSON file to location-analyzer web interface
1. **Real-time progress updates** - critical for user experience during processing
1. **Intelligent geocoding with caching** - avoids repeated API calls for known locations
1. **User-configurable analysis settings** for optimized output
1. Statistical calculations and movement analysis
1. Export generation in multiple formats

### Geocoding & Caching Strategy

- **API call optimization**: Cache all geocoding results locally
- **Avoid redundant calls**: Check cache before making new API requests
- **Performance boost**: Significantly faster processing on subsequent runs
- **Cost efficiency**: Reduces API usage and associated costs

### Output Files Generated

- **city_jumps.csv**: Movement between cities with distances and timing
- **by_city_location_days.csv**: Time spent in each city
- **by_state_location_days.csv**: Time spent in each state/country
- **analysis_summary.txt**: Overview with top destinations

## Code Style & Conventions

### Python Standards

- Follow PEP 8 styling guidelines
- Use async/await for API processing where applicable
- Implement proper error handling for API calls
- Use descriptive variable names for location data
- Add docstrings for complex analysis functions

### File Organization

- **Primary interface**: `app.py` (web application - main focus)
- **Legacy interface**: `gui_app.py` (desktop - deprecated)
- Configuration files in `config/` directory
- Output files generated in project root
- **Companion preprocessing app** - separate tool for cleaning raw Google JSON
- **Cache files** - store geocoding results for reuse

### Data Processing Patterns

- **Two-stage processing**: Raw Google JSON → Preprocessed JSON → Analysis
- **Progress feedback loops** - constantly update user on processing status
- **Cache-first geocoding** - check local cache before API calls
- **User setting integration** - allow runtime configuration of analysis parameters

### API Usage Best Practices

- **Implement intelligent caching** to reduce API calls (CRITICAL FEATURE)
- **Always check cache first** before making geocoding requests
- Use async processing for bulk geocoding requests
- Handle rate limiting gracefully
- Provide fallback for failed geocoding requests
- **Cache persistence** - save cache between sessions for maximum efficiency

### User Experience Priorities

- **Progress tracking is essential** - users need constant feedback during processing
- **Configurable settings** - allow users to optimize analysis parameters
- **Real-time updates** - show processing status, current operation, completion percentage
- **Clear error handling** - inform users of issues without technical jargon

## Development Workflow

### Testing Approach

- Test with sample location data before full dataset
- Verify API key configuration before processing
- Check output file generation and format
- Validate distance calculations and time analysis

### Performance Considerations

- Use async/await for concurrent API requests
- Implement caching for repeated location lookups
- Progress tracking for user feedback during processing
- Memory-efficient processing for large datasets

### Privacy & Security

- All processing happens locally on user machine
- No location data transmitted beyond geocoding API calls
- API keys stored in local configuration files
- No persistent storage of sensitive location data

## Common Development Tasks

### Adding New Analysis Features

- Extend the analysis engine in the main web processing modules
- **Update web interface** for new outputs (primary focus)
- Add corresponding CSV export functionality
- **Update progress tracking** for new processing steps (critical for UX)
- Consider impact on user-configurable settings

### Geocoding & Caching Enhancements

- **Cache management** - implement cache cleanup, optimization
- Geoapify API integration improvements
- Consider backup geocoding services for reliability
- **Cache persistence strategies** - file-based, database options
- **Cache invalidation** - handle stale or incorrect cached data

### User Experience Improvements

- **Progress tracking refinements** - more granular status updates
- **Settings interface** - make user configuration more intuitive
- Web interface responsiveness and real-time feedback
- **Error handling** - graceful degradation when API calls fail
- **Performance metrics** - show processing speed, cache hit rates

## Dependencies & External Services

- Flask for web framework
- Geoapify for geocoding services
- Standard Python libraries for data processing
- Modern web technologies for frontend interface

## Deployment Notes

- Designed for local execution (not web deployment)
- Desktop and web interfaces for different use cases
- No server-side hosting required
- All processing happens on user’s machine

## Contributing Guidelines

- Follow existing code structure and patterns
- Test with various location dataset sizes
- Maintain both web and desktop interface compatibility
- Document any new API integrations or features
- Ensure privacy-focused approach is maintained

## Troubleshooting Common Issues

- **API Key Issues**: Verify Geoapify key in config/web_config.json
- **Wrong Data Source**: Ensure using NEW mobile exporter, not Google Takeout
- **Raw vs. Processed Data**: Verify JSON has been cleaned by preprocessing app
- **Cache Issues**: Check cache file permissions and corruption
- **Progress Stalling**: Monitor API rate limits and network connectivity
- **Settings Problems**: Validate user configuration parameters
- **Performance**: Large datasets require patience; check cache utilization

## Important Notes for Development

1. **Web-first approach** - desktop GUI is legacy, focus on web interface
1. **Progress feedback is critical** - users processing large files need constant updates
1. **Cache optimization** - major performance and cost factor
1. **Two-stage data processing** - prefer to use preprocessed JSON, never raw Google export because the raw output has noisy data.
1. **User settings** - make analysis configurable for different use cases
1. **Error resilience** - handle API failures gracefully without losing progress
1. ** we need to improve date picking error avoidance by pre-selecting dates that exist in the file we are processing, and making the “from” date always before to “to” date

-----

*This project processes Google Location History data locally with focus on privacy, performance, and detailed travel analytics.*

