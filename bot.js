require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');

const botToken = process.env.BOT_TOKEN;
if (!botToken) {
  console.error('BOT_TOKEN not set!');
  process.exit(1);
}

const bot = new TelegramBot(botToken, { polling: true });

bot.on('message', async (msg) => {
  // আপনি চাইলে এখানে অতিরিক্ত লজিক যোগ করতে পারেন
  // উদাহরণ: যদি ব্যবহারকারী /start পাঠায়, স্বাগতম বার্তা পাঠান
  if (msg.text && msg.text.toLowerCase() === '/start') {
    bot.sendMessage(msg.chat.id, 'Welcome to RTX Lock Tool Bot!');
  }

  // যদি চ্যাটে কোনো ফটো পাঠানো হয়
  if (msg.photo) {
    const fileId = msg.photo[msg.photo.length - 1].file_id;
    const fileLink = await bot.getFileLink(fileId);
    console.log(`Received photo: ${fileLink}`);
    // এখানে আপনি ফটো ডাউনলোড করে, সংরক্ষণ বা প্রক্রিয়া করতে পারেন
  }
});

console.log('🤖 Telegram bot is running...');
