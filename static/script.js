document.querySelector('form').addEventListener('submit', (e) => {
    e.preventDefault(); // Prevent form from refreshing the page
    const formData = new FormData(e.target); // Get form data

    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json()) // Parse JSON response
    .then(data => {
        const messageDiv = document.getElementById('message');
        if (data.success) {
            // Display extracted text
            messageDiv.innerHTML = `
                <p style="color: green;">Extracted Text:</p>
                <pre>${data.text}</pre>
            `;
        } else {
            // Display error message
            messageDiv.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const messageDiv = document.getElementById('message');
        messageDiv.innerHTML = `<p style="color: red;">An unexpected error occurred.</p>`;
    });
});
