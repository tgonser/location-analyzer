# app.py - Enhanced Flask Application with Real-time Processing Feedback (Final Version)
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, Response
import os
import json
from datetime import date, datetime
from werkzeug.utils import secure_filename
import sys
import traceback
import threading
import time
import uuid

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from analyzer_bridge import process_location_file
    ANALYZER_AVAILABLE = True
    print("SUCCESS: Location analyzer imported")
except ImportError as e:
    print(f"WARNING: Could not import analyzer: {e}")
    ANALYZER_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'change-this-secret-key-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Config file for web app settings
WEB_CONFIG_FILE = "config/web_config.json"

# Global storage for analysis progress
analysis_progress = {}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs('config', exist_ok=True)

def load_web_config():
    """Load web app configuration"""
    if os.path.exists(WEB_CONFIG_FILE):
        try:
            with open(WEB_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"WARNING: Failed to load web config: {e}")
            return {}
    return {}

def save_web_config(config):
    """Save web app configuration"""
    try:
        with open(WEB_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"WARNING: Failed to save web config: {e}")

def parse_date_string(date_str):
    """Safely parse date string to date object"""
    try:
        if isinstance(date_str, date):
            return date_str
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError) as e:
        print(f"WARNING: Could not parse date '{date_str}': {e}")
        return date.today()
    return date.today()

@app.route('/')
def index():
    config = load_web_config()
    
    # Get saved values or defaults
    default_start = config.get("last_start_date", "2024-01-01")
    default_end = config.get("last_end_date", date.today().strftime('%Y-%m-%d'))
    default_geoapify = config.get("geoapify_key", "")
    default_google = config.get("google_key", "")
    
    return render_template('index.html', 
                         analyzer_available=ANALYZER_AVAILABLE,
                         today=date.today().strftime('%Y-%m-%d'),
                         default_start_date=default_start,
                         default_end_date=default_end,
                         default_geoapify_key=default_geoapify,
                         default_google_key=default_google)

@app.route('/upload', methods=['POST'])
def upload_file():
    print("DEBUG: Upload route called")
    
    if not ANALYZER_AVAILABLE:
        flash('Location analyzer is not available. Please check setup.', 'error')
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if file and file.filename.endswith('.json'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"DEBUG: File saved to {filepath}")
        
        # Get form data and parse dates properly
        start_date_str = request.form.get('start_date', str(date.today()))
        end_date_str = request.form.get('end_date', str(date.today()))
        geoapify_key = request.form.get('geoapify_key', '')
        google_key = request.form.get('google_key', '')
        
        # Convert string dates to date objects
        start_date = parse_date_string(start_date_str)
        end_date = parse_date_string(end_date_str)
        
        # Save configuration for next time
        config = load_web_config()
        config.update({
            "last_start_date": start_date_str,
            "last_end_date": end_date_str,
            "geoapify_key": geoapify_key,
            "google_key": google_key
        })
        save_web_config(config)
        
        if not geoapify_key.strip():
            flash('Geoapify API key is required', 'error')
            return redirect(url_for('index'))
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        print(f"DEBUG: Generated analysis_id: {analysis_id}")
        
        # Initialize progress tracking
        analysis_progress[analysis_id] = {
            'status': 'starting',
            'message': 'Initializing analysis...',
            'progress': 0,
            'logs': [],
            'result': None,
            'output_dir': None,
            'error': None,
            'complete': False
        }
        print(f"DEBUG: Created progress entry for {analysis_id}")
        
        # Start analysis in background thread
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], 
                                f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(output_dir, exist_ok=True)
        
        thread = threading.Thread(
            target=run_analysis_thread,
            args=(analysis_id, filepath, start_date, end_date, output_dir, 
                  geoapify_key, google_key, filename)
        )
        thread.daemon = True
        thread.start()
        print(f"DEBUG: Started background thread for {analysis_id}")
        
        # Redirect to processing page
        print(f"DEBUG: About to redirect to /processing/{analysis_id}")
        return redirect(url_for('processing', analysis_id=analysis_id))
    
    else:
        flash('Please upload a JSON file', 'error')
        return redirect(url_for('index'))

def run_analysis_thread(analysis_id, filepath, start_date, end_date, output_dir, 
                       geoapify_key, google_key, filename):
    """Run the analysis in a background thread with progress updates"""
    print(f"DEBUG: Analysis thread started for {analysis_id}")
    try:
        def progress_log(msg):
            """Log function that updates progress"""
            print(f"DEBUG: Progress log for {analysis_id}: {msg}")
            if analysis_id in analysis_progress:
                analysis_progress[analysis_id]['logs'].append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': msg
                })
                analysis_progress[analysis_id]['message'] = msg
                
                # Update progress based on message content
                if 'Starting analysis' in msg:
                    analysis_progress[analysis_id]['progress'] = 10
                elif 'Found' in msg and 'location points' in msg:
                    analysis_progress[analysis_id]['progress'] = 20
                elif 'Filtered to' in msg:
                    analysis_progress[analysis_id]['progress'] = 30
                elif 'Geocoded' in msg:
                    analysis_progress[analysis_id]['progress'] = 70
                elif 'Total distance' in msg:
                    analysis_progress[analysis_id]['progress'] = 85
                elif 'exported' in msg:
                    analysis_progress[analysis_id]['progress'] = 95
        
        def cancel_check():
            return False  # No cancellation for web version
        
        # Update status
        analysis_progress[analysis_id]['status'] = 'running'
        analysis_progress[analysis_id]['message'] = 'Processing location data...'
        analysis_progress[analysis_id]['progress'] = 5
        print(f"DEBUG: Updated progress for {analysis_id} to 5%")
        
        # Run the location analysis
        result = process_location_file(
            filepath,
            start_date,
            end_date,
            output_dir,
            "by_city",  # group_by
            geoapify_key,
            google_key,
            "",  # onwater_key
            0.1,  # delay
            1,    # batch_size
            progress_log,
            cancel_check,
            True  # include_distance
        )
        
        print(f"DEBUG: Analysis completed for {analysis_id}, result: {result}")
        
        if result is not None:
            # Get list of generated files
            generated_files = []
            if os.path.exists(output_dir):
                for f in os.listdir(output_dir):
                    if f.endswith('.csv') or f.endswith('.txt'):
                        generated_files.append(f)
            
            # Update final progress
            analysis_progress[analysis_id].update({
                'status': 'completed',
                'message': 'Analysis completed successfully!',
                'progress': 100,
                'result': result,
                'output_dir': os.path.basename(output_dir),
                'generated_files': generated_files,
                'complete': True,
                'filename': filename,
                'date_range': f"{start_date} to {end_date}"
            })
            print(f"DEBUG: Final update completed for {analysis_id}")
        else:
            analysis_progress[analysis_id].update({
                'status': 'error',
                'message': 'Analysis failed',
                'progress': 0,
                'error': 'Analysis returned no results',
                'complete': True
            })
            print(f"DEBUG: Analysis failed for {analysis_id}")
            
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        print(f"DEBUG: Exception in analysis thread for {analysis_id}: {error_msg}")
        analysis_progress[analysis_id].update({
            'status': 'error',
            'message': error_msg,
            'progress': 0,
            'error': error_msg,
            'complete': True
        })

@app.route('/processing/<analysis_id>')
def processing(analysis_id):
    """Show the real-time processing page"""
    print(f"DEBUG: Processing route called with analysis_id: {analysis_id}")
    
    if analysis_id not in analysis_progress:
        print(f"DEBUG: Analysis {analysis_id} not found in progress dict")
        print(f"DEBUG: Available analysis IDs: {list(analysis_progress.keys())}")
        flash('Analysis not found', 'error')
        return redirect(url_for('index'))
    
    print(f"DEBUG: Rendering processing.html for {analysis_id}")
    try:
        return render_template('processing.html', analysis_id=analysis_id)
    except Exception as e:
        print(f"DEBUG: Error rendering processing.html: {e}")
        return f"Error loading processing page: {e}"

@app.route('/progress/<analysis_id>')
def get_progress(analysis_id):
    """API endpoint to get analysis progress"""
    print(f"DEBUG: Progress API called for {analysis_id}")
    
    if analysis_id not in analysis_progress:
        print(f"DEBUG: Analysis {analysis_id} not found for progress API")
        return jsonify({'error': 'Analysis not found'}), 404
    
    progress_data = analysis_progress[analysis_id].copy()
    print(f"DEBUG: Returning progress data: {progress_data['progress']}% - {progress_data['message']}")
    
    return jsonify(progress_data)

@app.route('/results/<analysis_id>')
def results(analysis_id):
    """Show final results page"""
    print(f"DEBUG: Results route called for {analysis_id}")
    
    if analysis_id not in analysis_progress:
        flash('Analysis not found', 'error')
        return redirect(url_for('index'))
    
    progress_data = analysis_progress[analysis_id]
    
    if not progress_data['complete']:
        print(f"DEBUG: Analysis {analysis_id} not complete, redirecting to processing")
        return redirect(url_for('processing', analysis_id=analysis_id))
    
    return render_template('results.html', 
                         result=progress_data.get('result'),
                         logs=[log['message'] for log in progress_data.get('logs', [])],
                         output_dir=progress_data.get('output_dir'),
                         generated_files=progress_data.get('generated_files', []),
                         success=progress_data['status'] == 'completed')

@app.route('/download/<path:output_dir>/<path:filename>')
def download_file(output_dir, filename):
    """Download generated files"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], output_dir, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('File not found', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/clear_config', methods=['POST'])
def clear_config():
    """Clear saved configuration"""
    try:
        if os.path.exists(WEB_CONFIG_FILE):
            os.remove(WEB_CONFIG_FILE)
        flash('Configuration cleared successfully', 'success')
    except Exception as e:
        flash(f'Failed to clear configuration: {str(e)}', 'error')
    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'analyzer_available': ANALYZER_AVAILABLE,
        'uploads_dir': os.path.exists(app.config['UPLOAD_FOLDER']),
        'outputs_dir': os.path.exists(app.config['OUTPUT_FOLDER'])
    }

@app.route('/test-processing')
def test_processing():
    """Test route to verify processing page works"""
    test_id = "test-123"
    analysis_progress[test_id] = {
        'status': 'running',
        'message': 'Test analysis in progress...',
        'progress': 50,
        'logs': [
            {'timestamp': '12:34:56', 'message': 'Starting test analysis'},
            {'timestamp': '12:35:10', 'message': 'Processing test data'},
        ],
        'complete': False
    }
    print(f"DEBUG: Created test analysis with ID: {test_id}")
    return redirect(url_for('processing', analysis_id=test_id))

if __name__ == '__main__':
    print("Starting Location Analyzer Web Application")
    print(f"   Analyzer available: {ANALYZER_AVAILABLE}")
    print(f"   Config file: {WEB_CONFIG_FILE}")
    print(f"   Access at: http://localhost:5000")
    
    # Show available routes
    print("DEBUG: Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)  # Enable debug mode for better error messages