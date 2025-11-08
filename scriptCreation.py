import os
import csv
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv('airia_url.env')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'csv', 'json', 'md'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_csv_knowledge_graph(file_path):
    """
    Validate that the CSV file is a valid knowledge graph format
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        dict with validation info (rows, columns, sample data)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                raise ValueError("CSV file is empty")
            
            # Get column names
            columns = list(rows[0].keys())
            
            return {
                'valid': True,
                'row_count': len(rows),
                'columns': columns,
                'sample_row': rows[0] if rows else None
            }
    except Exception as e:
        raise ValueError(f"Invalid CSV format: {str(e)}")

def run_airia_agent(knowledge_graph_path, x_value):
    """
    Run the Airia agent with a knowledge graph CSV file and prompt template
    
    Args:
        knowledge_graph_path: Path to the CSV knowledge graph file
        x_value: Value to replace {x} in the prompt template
    
    Returns:
        Response from Airia API
    """
    # Get Airia API URL from environment
    airia_url = os.getenv('AIRIA_URL', '').strip()
    
    if not airia_url:
        raise ValueError("AIRIA_URL not found in environment variables")
    
    # Validate the CSV knowledge graph
    csv_info = validate_csv_knowledge_graph(knowledge_graph_path)
    
    # Format the prompt with the x value
    prompt = f"Tell me about {x_value}"
    
    # Prepare the request
    # Read the CSV file content
    with open(knowledge_graph_path, 'rb') as f:
        files = {
            'file': (os.path.basename(knowledge_graph_path), f, 'text/csv')
        }
        
        data = {
            'user_input': prompt
        }
        
        # Make the API request
        try:
            response = requests.post(
                airia_url,
                files=files,
                data=data,
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Airia API: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/process', methods=['POST'])
def process_file():
    """
    Process a knowledge graph CSV file with Airia agent
    
    Expected form data:
    - file: The CSV knowledge graph file to process
    - x: The value to replace {x} in the prompt template
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if x value is provided
        x_value = request.form.get('x')
        if not x_value:
            return jsonify({'error': 'No x value provided'}), 400
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is a CSV
        if not file.filename.lower().endswith('.csv'):
            return jsonify({
                'error': 'File must be a CSV file. Knowledge graphs should be in CSV format.'
            }), 400
        
        # Save the CSV file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Validate the CSV knowledge graph
            csv_info = validate_csv_knowledge_graph(file_path)
            
            # Run Airia agent with the knowledge graph
            result = run_airia_agent(file_path, x_value)
            
            # Clean up uploaded file
            os.remove(file_path)
            
            return jsonify({
                'success': True,
                'result': result,
                'prompt_used': f"Tell me about {x_value}",
                'knowledge_graph_info': {
                    'row_count': csv_info['row_count'],
                    'columns': csv_info['columns']
                }
            }), 200
            
        except ValueError as e:
            # Clean up uploaded file on validation error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            # Clean up uploaded file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

