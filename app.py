import sqlite3
import random
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
DB_NAME = "database.db"

WHATSAPP_NUMBER = "27815909460"
WHATSAPP_DISPLAY = "081 590 9460"

ALL_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
    "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM",
    "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM",
    "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM",
    "05:00 PM", "05:30 PM"
]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            surname TEXT NOT NULL,
            whatsapp TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            reference_code TEXT NOT NULL,
            status TEXT DEFAULT 'Pending Arrival',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skêr Barber Co. | Student Booking</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 font-sans antialiased min-h-screen flex flex-col justify-between">
    <div class="max-w-md mx-auto w-full p-6 my-auto">
        <div class="text-center mb-8">
            <span class="bg-amber-500/10 text-amber-400 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">Stellenbosch Special</span>
            <h1 class="text-3xl font-bold tracking-tight mt-3">Skêr Barber Co.</h1>
            <p class="text-zinc-400 text-sm mt-1">Lock in your student fade. Skip the line.</p>
        </div>

        <form action="/book" method="POST" class="space-y-4 bg-zinc-900 border border-zinc-800 p-6 rounded-2xl shadow-xl">
            <div>
                <label class="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">First Name</label>
                <input type="text" name="first_name" required class="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-amber-500 transition">
            </div>
            <div>
                <label class="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">Surname</label>
                <input type="text" name="surname" required class="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-amber-500 transition">
            </div>
            <div>
                <label class="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">WhatsApp Number</label>
                <input type="tel" name="whatsapp" placeholder="081 590 9460" required class="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-amber-500 transition">
            </div>
            <div>
                <label class="block text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">Select Available Time Slot</label>
                <select name="time_slot" required class="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-amber-500 transition">
                    <option value="" disabled selected>Choose available time</option>
                    {% for slot in all_slots %}
                        {% if slot in booked_slots %}
                            <option value="{{ slot }}" disabled class="text-zinc-600 bg-zinc-950">{{ slot }} — [BOOKED]</option>
                        {% else %}
                            <option value="{{ slot }}">{{ slot }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
            </div>
            <button type="submit" class="w-full bg-amber-500 hover:bg-amber-400 text-zinc-950 font-semibold py-3 rounded-xl transition shadow-lg mt-2">
                Lock In Booking
            </button>
        </form>
        <div class="text-center mt-6">
            <a href="/qr-codes" class="text-xs text-zinc-500 hover:text-amber-400 transition underline">View Shop QR Codes</a>
        </div>
    </div>
    <footer class="text-center py-4 text-xs text-zinc-600">
        Flux Booking Engine &bull; Stellenbosch
    </footer>
</body>
</html>
'''

SUCCESS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmed | Skêr Barber Co.</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 font-sans antialiased min-h-screen flex flex-col justify-between">
    <div class="max-w-md mx-auto w-full p-6 my-auto text-center">
        <div class="bg-zinc-900 border border-zinc-800 p-8 rounded-2xl shadow-xl">
            <div class="w-12 h-12 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 text-xl">✓</div>
            <h1 class="text-2xl font-bold tracking-tight">Booking Secured!</h1>
            <p class="text-zinc-400 text-sm mt-2">Show this unique QR code to the barber when you sit in the chair:</p>
            
            <!-- UNIQUE DYNAMIC QR CODE DISPLAYED ON CLIENT PHONE -->
            <div class="my-6 bg-white p-4 rounded-2xl inline-block shadow-inner">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={{ verify_url }}" alt="Personal QR Pass" class="mx-auto rounded-lg">
            </div>

            <div class="mb-6">
                <span class="text-2xl font-mono font-bold text-amber-400 tracking-wider">{{ ref }}</span>
            </div>

            <a href="https://wa.me/{{ wa_number }}?text=Hi!%20I%20just%20booked%20via%20Flux.%0AMy%20Ref:%20{{ ref }}%0AName:%20{{ name }}%0ATime:%20{{ time }}" 
               target="_blank" 
               class="block w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-xl transition text-sm mb-3 shadow-lg flex items-center justify-center gap-2">
                <span>💬 Send Booking via WhatsApp ({{ wa_display }})</span>
            </a>

            <a href="/" class="block w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-medium py-3 rounded-xl transition text-sm">
                Back to Home
            </a>
        </div>
    </div>
</body>
</html>
'''

QR_HUB_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shop QR Codes Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 font-sans antialiased p-6">
    <div class="max-w-3xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-2xl font-bold tracking-tight">Shop QR Codes Hub</h1>
                <p class="text-zinc-400 text-sm">The two core QR codes for your booking and verification workflow.</p>
            </div>
            <a href="/" class="bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold px-4 py-2 rounded-xl transition">Home</a>
        </div>

        <div class="grid md:grid-cols-2 gap-6">
            <!-- QR 1: Booking QR -->
            <div class="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl text-center shadow-xl">
                <span class="bg-amber-500/10 text-amber-400 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">QR Code 1</span>
                <h2 class="text-lg font-bold mt-3">Booking Poster QR</h2>
                <p class="text-zinc-400 text-xs mt-1 mb-4">Print this and stick it on your mirror or door so clients can scan to book.</p>
                <div class="bg-white p-4 rounded-2xl inline-block shadow-inner mb-4">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={{ booking_url }}" alt="Booking QR" class="mx-auto rounded-lg">
                </div>
                <div class="text-xs font-mono text-zinc-500 break-all">{{ booking_url }}</div>
            </div>

            <!-- QR 2: Example Personal Check-in QR -->
            <div class="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl text-center shadow-xl">
                <span class="bg-emerald-500/10 text-emerald-400 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">QR Code 2</span>
                <h2 class="text-lg font-bold mt-3">Client Pass QR (Example)</h2>
                <p class="text-zinc-400 text-xs mt-1 mb-4">Generated dynamically on each client's phone after booking for the barber to scan.</p>
                <div class="bg-white p-4 rounded-2xl inline-block shadow-inner mb-4">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={{ sample_verify_url }}" alt="Sample Pass QR" class="mx-auto rounded-lg">
                </div>
                <div class="text-xs font-mono text-zinc-500 break-all">Encodes: /verify-pass/AW999</div>
            </div>
        </div>
        
        <div class="mt-8 text-center">
            <a href="/admin" class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-6 py-3 rounded-xl transition text-sm shadow-lg inline-block">
                View Master Dashboard 📊
            </a>
        </div>
    </div>
</body>
</html>
'''

VERIFY_SUCCESS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cut Verified Successfully</title>
    <script src="https://tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 font-sans antialiased min-h-screen flex flex-col justify-between">
    <div class="max-w-md mx-auto w-full p-6 my-auto text-center">
        <div class="bg-zinc-900 border border-zinc-800 p-8 rounded-2xl shadow-xl">
            <div class="w-12 h-12 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 text-xl">✓</div>
            <h1 class="text-2xl font-bold tracking-tight">Verified & Logged!</h1>
            <p class="text-zinc-400 text-sm mt-2">Reference <span class="font-mono font-bold text-amber-400">{{ ref }}</span> has been marked as a completed cut.</p>
            <div class="mt-6">
                <a href="/admin" class="block w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3 rounded-xl transition text-sm">
                    View Master Dashboard
                </a>
            </div>
        </div>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Reconciliation Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 font-sans antialiased p-6">
    <div class="max-w-5xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-2xl font-bold tracking-tight">Agency Master Dashboard</h1>
                <p class="text-zinc-400 text-sm">Verified customer passes scanned directly from client phones.</p>
            </div>
            <div class="flex gap-2">
                <a href="/qr-codes" class="bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold px-4 py-2 rounded-xl transition">QR Hub</a>
                <a href="/" class="bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold px-4 py-2 rounded-xl transition">Landing Page</a>
            </div>
        </div>

        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl">
            <table class="w-full text-left border-collapse text-sm">
                <thead>
                    <tr class="border-b border-zinc-800 text-zinc-400 text-xs uppercase tracking-wider bg-zinc-950/50">
                        <th class="p-4">Ref Code</th>
                        <th class="p-4">Client Name</th>
                        <th class="p-4">WhatsApp</th>
                        <th class="p-4">Time Slot</th>
                        <th class="p-4">Status</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-zinc-800">
                    {% for lead in leads %}
                    <tr class="hover:bg-zinc-800/30 transition">
                        <td class="p-4 font-mono font-bold text-amber-400">{{ lead[5] }}</td>
                        <td class="p-4 font-medium">{{ lead[1] }} {{ lead[2] }}</td>
                        <td class="p-4 text-zinc-400">{{ lead[3] }}</td>
                        <td class="p-4 text-zinc-300">{{ lead[4] }}</td>
                        <td class="p-4">
                            {% if lead[6] == 'Completed & Verified' %}
                                <span class="bg-emerald-500/10 text-emerald-400 text-xs px-2.5 py-1 rounded-full font-medium">Completed & Verified</span>
                            {% else %}
                                <span class="bg-amber-500/10 text-amber-400 text-xs px-2.5 py-1 rounded-full font-medium">Pending Arrival</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="p-8 text-center text-zinc-500">No leads recorded yet.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT time_slot FROM leads')
    booked_slots = [row[0] for row in cursor.fetchall()]
    conn.close()
    return render_template_string(INDEX_TEMPLATE, all_slots=ALL_SLOTS, booked_slots=booked_slots)

@app.route('/book', methods=['POST'])
def book():
    first_name = request.form.get('first_name')
    surname = request.form.get('surname')
    whatsapp = request.form.get('whatsapp').strip()
    time_slot = request.form.get('time_slot')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM leads WHERE time_slot = ?', (time_slot,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return "Error: That time slot was just booked by someone else! Go back and choose another.", 400

    ref_code = f"AW{random.randint(100, 999)}"
    
    cursor.execute('''
        INSERT INTO leads (first_name, surname, whatsapp, time_slot, reference_code, status)
        VALUES (?, ?, ?, ?, ?, 'Pending Arrival')
    ''', (first_name, surname, whatsapp, time_slot, ref_code))
    conn.commit()
    conn.close()

    verify_url = url_for('verify_pass', ref_code=ref_code, _external=True)

    return render_template_string(
        SUCCESS_TEMPLATE, 
        ref=ref_code, 
        name=f"{first_name} {surname}", 
        time=time_slot, 
        verify_url=verify_url,
        wa_number=WHATSAPP_NUMBER,
        wa_display=WHATSAPP_DISPLAY
    )

@app.route('/qr-codes')
def qr_codes():
    booking_url = url_for('index', _external=True)
    sample_verify_url = url_for('verify_pass', ref_code='AW999', _external=True)
    return render_template_string(QR_HUB_TEMPLATE, booking_url=booking_url, sample_verify_url=sample_verify_url)

@app.route('/verify-pass/<ref_code>')
def verify_pass(ref_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET status = 'Completed & Verified' WHERE reference_code = ?", (ref_code,))
    conn.commit()
    conn.close()
    return render_template_string(VERIFY_SUCCESS_TEMPLATE, ref=ref_code)

@app.route('/admin')
def admin():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leads ORDER BY id DESC')
    leads = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, leads=leads)

import os

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)