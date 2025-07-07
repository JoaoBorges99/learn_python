const form = document.getElementById('uploadForm');
const msg = document.getElementById('msg');
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    msg.textContent = '';
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) {
        msg.textContent = 'Selecione um arquivo.';
        return;
    }
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    try {
        const response = await fetch('/graficos_excel', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.url) {
            window.location.href = data.url;
        } else {
            msg.textContent = data.error || data.erro || 'Erro ao processar o arquivo.';
        }
    } catch (err) {
        msg.textContent = 'Erro ao enviar o arquivo.';
    }
});