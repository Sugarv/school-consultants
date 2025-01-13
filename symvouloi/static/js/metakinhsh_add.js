document.addEventListener('DOMContentLoaded', () => {
  // Select only the specific button for AJAX submission
  const ajaxButton = document.querySelector('.add-metak-btn');
  
  if (ajaxButton) {
      ajaxButton.addEventListener('click', async (e) => {
          // Prevent default form submission or link navigation
          e.preventDefault();
          
          // Get the form (if button is inside a form)
          const form = ajaxButton.closest('form');
          
          // Hardcoded URL - you'll want to customize this
          const url = '/add_metakinhsh';
          
          // Prepare form data
          const formData = form ? new FormData(form) : new FormData();
          
          // Message container (create if not exists)
          let messageContainer = document.getElementById('ajax-message');
          if (!messageContainer) {
              messageContainer = document.createElement('div');
              messageContainer.id = 'ajax-message';
              messageContainer.classList.add('fixed', 'top-4', 'left-1/2', 'transform', '-translate-x-1/2', 'z-50');
              document.body.appendChild(messageContainer);
          }
          
          // Disable button during submission
          ajaxButton.disabled = true;
          
          try {
              // Send request
              const response = await fetch(url, {
                  method: 'POST',
                  body: formData,
                  headers: {
                      'X-Requested-With': 'XMLHttpRequest',
                      'X-CSRFToken': getCookie('csrftoken')
                  }
              });
              
              // Parse response
              const result = await response.json();
              
              // Display message
              messageContainer.innerHTML = `
                  <div class="bg-${result.success ? 'green' : 'red'}-500 text-white px-4 py-2 rounded shadow-lg">
                      ${result.message}
                  </div>
              `;
              
              // Auto-hide message after 3 seconds
              setTimeout(() => {
                  messageContainer.innerHTML = '';
              }, 3000);
              
              // Optional: reset form or perform additional actions
              if (result.success && form) {
                  form.reset();
              }
          } catch (error) {
              // Handle network or parsing errors
              messageContainer.innerHTML = `
                  <div class="bg-red-500 text-white px-4 py-2 rounded shadow-lg">
                      An error occurred. Please try again.
                  </div>
              `;
              console.error('Submission error:', error);
          } finally {
              // Re-enable button
              ajaxButton.disabled = false;
          }
      });
  }
  
  // Helper function to get CSRF cookie
  function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
              const cookie = cookies[i].trim();
              if (cookie.substring(0, name.length + 1) === (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }
});