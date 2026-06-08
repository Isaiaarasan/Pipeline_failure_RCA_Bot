1. Activate the Virtual Environment
The project has a virtual environment set up (.venv). It is highly recommended to activate it first:

powershell
.venv\Scripts\activate
2. Install Dependencies
If you haven't already, install the required Python packages:

powershell
pip install -r requirements.txt
3. Check Configuration
Ensure your .env file (which is already present in your project root) has the necessary configurations like your DATABASE_URL, OLLAMA_API_URL, and GITHUB_TOKEN.

4. Run the Application
Start the Flask development web server by running:

powershell
python app.py
5. Access the Web Interface
Once the server is running, open your web browser and go to: http://localhost:5000
