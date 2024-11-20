// Your existing JavaScript for news fetching

// Modal handling
const modal = document.getElementById('login-modal');
const openModalButton = document.getElementById('open-login-modal');
const closeButton = document.querySelector('.close-button');
const loginForm = document.getElementById('login-form');

// Show modal when button is clicked
openModalButton.onclick = function() {
    modal.style.display = 'block';
};

// Close modal when the close button is clicked
closeButton.onclick = function() {
    modal.style.display = 'none';
};

// Close modal when clicking outside the modal
window.onclick = function(event) {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
};

// Handle form submission
loginForm.onsubmit = function(event) {
    event.preventDefault(); // Prevent form from submitting the traditional way

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Send login details to server
    fetch('/login', { // Updated to point to your Flask endpoint
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Login successful!');
            modal.style.display = 'none';
        } else {
            alert('Login failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again later.');
    });
};
