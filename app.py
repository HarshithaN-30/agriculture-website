from flask import Flask, request, render_template, redirect, url_for, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import math
from fpdf import FPDF
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management

DATABASE = 'terrafoster.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()

        if row and check_password_hash(row[0], password):
            session['username'] = username
            return redirect(url_for('analyze'))
        else:
            return render_template('login.html', message='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', message='Username already exists')
    
    return render_template('register.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        n = float(request.form['n'])
        p = float(request.form['p'])
        k = float(request.form['k'])
        moisture = float(request.form['moisture'])
        ph = float(request.form['ph'])
        crop = request.form['crop']

        cropFertilizerRequirements = {
            'rice': {'n': 120, 'p': 60, 'k': 40, 'ph': 5.5, 'moisture': 7.5, 'min_temp': 70, 'max_temp': 80},
            'sugarcane': {'n': 250, 'p': 75, 'k': 190, 'ph': 6.0, 'moisture': 7.0, 'min_temp': 60, 'max_temp': 70},
            'cotton': {'n': 120, 'p': 60, 'k': 60, 'ph': 5.8, 'moisture': 7.0, 'min_temp': 65, 'max_temp': 75},
            'ragi': {'n': 60, 'p': 35, 'k': 35, 'ph': 4.5, 'moisture': 6.5, 'min_temp': 60, 'max_temp': 80},
            'wheat': {'n': 150, 'p': 90, 'k': 60, 'ph': 6.0, 'moisture': 7.5, 'min_temp': 60, 'max_temp': 70},
            'maize': {'n': 150, 'p': 75, 'k': 60, 'ph': 5.5, 'moisture': 7.5, 'min_temp': 60, 'max_temp': 75},
            'potato': {'n': 100, 'p': 80, 'k': 120, 'ph': 5.0, 'moisture': 6.5, 'min_temp': 60, 'max_temp': 80},
            'tomato': {'n': 120, 'p': 50, 'k': 80, 'ph': 6.0, 'moisture': 6.8, 'min_temp': 60, 'max_temp': 75},
            'mango': {'n': 100, 'p': 50, 'k': 100, 'ph': 5.5, 'moisture': 7.5, 'min_temp': 50, 'max_temp': 70},
            'banana': {'n': 250, 'p': 60, 'k': 300, 'ph': 6.0, 'moisture': 7.0, 'min_temp': 75, 'max_temp': 85},
            'groundnut': {'n': 30, 'p': 60, 'k': 40, 'ph': 5.5, 'moisture': 7.0, 'min_temp': 60, 'max_temp': 70},
            'sunflower': {'n': 90, 'p': 60, 'k': 90, 'ph': 6.0, 'moisture': 7.5, 'min_temp': 50, 'max_temp': 65},
            'soybean': {'n': 50, 'p': 70, 'k': 30, 'ph': 6.0, 'moisture': 7.0, 'min_temp': 60, 'max_temp': 70},
            'chickpea': {'n': 20, 'p': 50, 'k': 20, 'ph': 6.0, 'moisture': 7.0, 'min_temp': 50, 'max_temp': 60},
            'onion': {'n': 100, 'p': 50, 'k': 80, 'ph': 6.0, 'moisture': 7.0, 'min_temp': 60, 'max_temp': 70},
            'cabbage': {'n': 120, 'p': 60, 'k': 120, 'ph': 6.0, 'moisture': 7.0, 'min_temp': 60, 'max_temp': 80},
            'carrot': {'n': 60, 'p': 40, 'k': 80, 'ph': 6.0, 'moisture': 6.8, 'min_temp': 55, 'max_temp': 65},
            'apple': {'n': 100, 'p': 50, 'k': 120, 'ph': 5.5, 'moisture': 7.0, 'min_temp': 50, 'max_temp': 70},
            'tea': {'n': 100, 'p': 60, 'k': 70, 'ph': 4.5, 'moisture': 5.5, 'min_temp': 65, 'max_temp': 75},
            'coffee': {'n': 120, 'p': 60, 'k': 80, 'ph': 5.0, 'moisture': 6.0, 'min_temp': 65, 'max_temp': 75},
        }

        def calculate_distance(soil_values, crop_values):
            return math.sqrt(
                (soil_values['n'] - crop_values['n']) ** 2 +
                (soil_values['p'] - crop_values['p']) ** 2 +
                (soil_values['k'] - crop_values['k']) ** 2 +
                (soil_values['ph'] - crop_values['ph']) ** 2
            )

        def get_ph_remedy(current_ph, recommended_ph):
            if current_ph < recommended_ph - 0.5:
                return "Increase soil pH by adding lime or using alkaline fertilizers."
            elif current_ph > recommended_ph + 0.5:
                return "Decrease soil pH by using sulfur or acid-forming fertilizers."
            else:
                return "Soil pH is within the recommended range."

        closest_crop = None
        min_distance = float('inf')
        for crop_name, crop_values in cropFertilizerRequirements.items():
            distance = calculate_distance(
                {'n': n, 'p': p, 'k': k, 'ph': ph},
                crop_values
            )
            if distance < min_distance:
                min_distance = distance
                closest_crop = crop_name

        recommended_crop_values = cropFertilizerRequirements[closest_crop]

        n_required = recommended_crop_values['n'] - n
        p_required = recommended_crop_values['p'] - p
        k_required = recommended_crop_values['k'] - k

        n_remedy = None
        p_remedy = None
        k_remedy = None

        if n_required < 0:
            n_remedy = "Consider planting nitrogen-fixing crops such as legumes or using cover crops to reduce excess nitrogen."
            n_required = abs(n_required)

        if p_required < 0:
            p_remedy = "Reduce phosphorus levels by using compost or organic matter with low phosphorus content."
            p_required = abs(p_required)

        if k_required < 0:
            k_remedy = "Consider using crops that can absorb excess potassium or use gypsum to help reduce potassium levels."
            k_required = abs(k_required)

        urea_required = n_required * 2.17
        ssp_required = p_required * 6.25
        mop_required = k_required * 1.66

        moisture_advice = None
        if moisture < 15:
            moisture_advice = "The soil moisture is low. Consider adding water to improve soil conditions."

        ph_advice = get_ph_remedy(ph, recommended_crop_values['ph'])

        suitable_crops = []
        for crop_name, crop_values in cropFertilizerRequirements.items():
            if crop_name != closest_crop:
                distance = calculate_distance(
                    {'n': n, 'p': p, 'k': k, 'ph': ph},
                    crop_values
                )
                if distance < min_distance * 1.2:  # Adjusted threshold for better crop suggestions
                    suitable_crops.append(crop_name)

        return redirect(url_for('recommendation', 
                                crop=closest_crop, 
                                n_required=n_required, 
                                p_required=p_required, 
                                k_required=k_required, 
                                urea_required=urea_required, 
                                ssp_required=ssp_required, 
                                mop_required=mop_required, 
                                moisture=moisture,
                                moisture_advice=moisture_advice,
                                ph_advice=ph_advice,
                                n_remedy=n_remedy,
                                p_remedy=p_remedy,
                                k_remedy=k_remedy,
                                recommended_crops=suitable_crops))
    
    return render_template('analyze.html')

@app.route('/recommendation')
def recommendation():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get parameters from the query string
    crop = request.args.get('crop')
    n_required = float(request.args.get('n_required', 0))
    p_required = float(request.args.get('p_required', 0))
    k_required = float(request.args.get('k_required', 0))
    urea_required = float(request.args.get('urea_required', 0))
    ssp_required = float(request.args.get('ssp_required', 0))
    mop_required = float(request.args.get('mop_required', 0))
    moisture = float(request.args.get('moisture', 0))  # Default to 0 if not provided
    moisture_advice = request.args.get('moisture_advice', '')
    ph_advice = request.args.get('ph_advice', '')
    n_remedy = request.args.get('n_remedy', '')
    p_remedy = request.args.get('p_remedy', '')
    k_remedy = request.args.get('k_remedy', '')
    recommended_crops = request.args.getlist('recommended_crops')  # Get the list of recommended crops

    return render_template('recommendation.html', 
                           crop=crop, 
                           n_required=n_required, 
                           p_required=p_required, 
                           k_required=k_required, 
                           urea_required=urea_required, 
                           ssp_required=ssp_required, 
                           mop_required=mop_required, 
                           moisture=moisture,
                           moisture_advice=moisture_advice,
                           ph_advice=ph_advice,
                           n_remedy=n_remedy,
                           p_remedy=p_remedy,
                           k_remedy=k_remedy,
                           closest_crop=crop,
                           recommended_crops=recommended_crops)
@app.route('/download_pdf')
def download_pdf():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Retrieve parameters from the query string
    crop = request.args.get('crop')
    n_required = float(request.args.get('n_required', 0))
    p_required = float(request.args.get('p_required', 0))
    k_required = float(request.args.get('k_required', 0))
    urea_required = float(request.args.get('urea_required', 0))
    ssp_required = float(request.args.get('ssp_required', 0))
    mop_required = float(request.args.get('mop_required', 0))
    moisture = float(request.args.get('moisture', 0))
    moisture_advice = request.args.get('moisture_advice', '')
    ph_advice = request.args.get('ph_advice', '')
    n_remedy = request.args.get('n_remedy', '')
    p_remedy = request.args.get('p_remedy', '')
    k_remedy = request.args.get('k_remedy', '')
    recommended_crops = request.args.getlist('recommended_crops')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Crop Recommendation Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Closest Crop: {crop}", ln=True)
    pdf.cell(200, 10, txt=f"N Required: {n_required} kg/ha", ln=True)
    pdf.cell(200, 10, txt=f"P Required: {p_required} kg/ha", ln=True)
    pdf.cell(200, 10, txt=f"K Required: {k_required} kg/ha", ln=True)
    pdf.cell(200, 10, txt=f"Urea Required: {urea_required} kg/ha", ln=True)
    pdf.cell(200, 10, txt=f"SSP Required: {ssp_required} kg/ha", ln=True)
    pdf.cell(200, 10, txt=f"MOP Required: {mop_required} kg/ha", ln=True)
    pdf.cell(200, 10, txt=f"Soil Moisture: {moisture}", ln=True)
    pdf.cell(200, 10, txt=f"Moisture Advice: {moisture_advice}", ln=True)
    pdf.cell(200, 10, txt=f"pH Advice: {ph_advice}", ln=True)
    
    pdf.ln(10)
    pdf.cell(200, 10, txt="Recommended Crops:", ln=True)
    for crop_name in recommended_crops:
        pdf.cell(200, 10, txt=f"- {crop_name}", ln=True)

    pdf_file = 'recommendation.pdf'
    pdf.output(pdf_file)

    # Send the PDF file to the user
    return send_file(pdf_file, as_attachment=True)

@app.route('/create_db', methods=['GET'])
def create_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()
    return 'Database created'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
