const fileInput = document.getElementById('fileInput');
const preview   = document.getElementById('preview');
const uploadBtn = document.getElementById('uploadBtn');

let selectedFile = null;

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (!file) return;

  selectedFile = file;

  const url = URL.createObjectURL(file);
  preview.src = url;
  preview.hidden = false;

  uploadBtn.disabled = false;
});

uploadBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  const formData = new FormData();
  formData.append('image', selectedFile);

  try {
    const resp = await fetch('/upload', { method: 'POST', body: formData });
    const data = await resp.json();

    if (data.ok) {
      alert('✅ Image uploaded to Telegram!');
    } else {
      alert('❌ Error: ' + (data.error || 'Unknown'));
    }
  } catch (err) {
    console.error(err);
    alert('❌ Network error');
  }
});
