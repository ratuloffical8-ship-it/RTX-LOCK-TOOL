# RTX Lock Tool

A tiny web app that lets a user capture a photo (camera or gallery) and forwards it to a Telegram bot.

## Features

- **Frontend**: Simple UI to pick an image, preview it, and upload.
- **Backend**: Express server that receives the image, forwards it to Telegram via Bot API.
- **Telegram Bot**: Runs alongside the server, can respond to `/start` and log received photos.

## Deployment on Render

1. **Create a new Web Service**  
   - GitHub repo: `rtx-lock-tool`  
   - Branch: `main`  
   - Build Command: `npm install`  
   - Start Command: `node server.js`  
   - **Environment Variables**  
     - `BOT_TOKEN` – Your bot token  
     - `ADMIN_CHAT_ID` – Chat ID to receive the photos

2. Render will automatically set `PORT` and serve the app over HTTPS.

3. After deployment, go to the URL, pick an image, hit **Upload to Bot** → you should see the photo in your Telegram chat.

## Local Development

```bash
git clone <repo>
cd rtx-lock-tool
npm install
echo "BOT_TOKEN=your_bot_token" > .env
echo "ADMIN_CHAT_ID=your_chat_id" >> .env
node server.js
