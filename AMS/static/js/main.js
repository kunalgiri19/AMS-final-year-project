function login() {
  var username = document.getElementById("user").value;
  var password = document.getElementById("pass").value;

  // Check if username or password is empty
  if (!username || !password) {
    showError("Please enter Username Password");
    return; // Stop further execution
  }

  fetch('/login', { // Removed the full URL to match the same origin
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username: username, password: password }),
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Incorrect Credentials');
    }
    return response.json();
  })
  .then(data => {
    alert(data.message);

    if (data.role === 'admin') {
      window.location.href = '/admin'; // Redirect to admin page
    } else if (data.role === 'user') {
      window.location.href = '/user'; // Redirect to user page
    } else if (data.role === 'staff') {
      window.location.href = '/staff'; // Redirect to staff page
    }
  })
  .catch((error) => {
    showError(error.message); // Display the error message in the error box
    console.error('Error:', error);
  });
}

document.addEventListener('DOMContentLoaded', function () {
  const errorBox = document.querySelector('.error');
  const errorTitle = document.querySelector('.error__title');
  const errorClose = document.querySelector('.error__close');

  errorClose.addEventListener('click', function () {
    hideError(); // Call the hideError function when the close button is clicked
  });
});

function showError(message) {
  const errorBox = document.querySelector('.error');
  const errorTitle = document.querySelector('.error__title');

  errorTitle.textContent = message;
  errorBox.classList.add('show'); // Show the error box
}

function hideError() {
  const errorBox = document.querySelector('.error');
  errorBox.classList.remove('show'); // Hide the error box
}

function logout() {
  fetch('/logout', { // Removed the full URL to match the same origin
    method: 'POST',
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Failed to logout!');
    }
    return response.json();
  })
  .then(data => {
    alert(data.message);
    window.location.href = '/'; // Redirect to home page after logout
  })
  .catch((error) => {
    alert('Failed to logout! Check console for details.');
    console.error('Error:', error);
  });
}

