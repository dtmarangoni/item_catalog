// Function to get a Cookie by name. It returns an empty string in case it's
// not found
function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}


// Sending data with fetch() only accepts form data in a FormData
// object (a construct set of key/value pairs representing form fields and
// their values. It uses the same format a form would use if the encoding type
// were set to "multipart/form-data").
// So this method is to prepare the form data to the acceptable encoding of
// fetch method.
function prepareFormData(form) {
    let data = new FormData();
    $.each(form.serializeArray(), function() {
        data.append(this.name, this.value);
    });
    data = new URLSearchParams(data);

    return data
}


// Asynchronous send the form data using fetch. The CSRF double submit value
// will be sent together with JWT token for authentication.
async function sendFormData() {
    // Form element
    const form = $('form');
    // Server url
    let url = form.attr('action');
    // HTTP method
    let method = form.attr('method');
    // CSRF double submit value used in JWT
    let header = {'X-CSRF-TOKEN': getCookie('csrf_access_token')};
    // form data
    data = prepareFormData(form);

    let init = {
        method: method,
        headers: header,
        body: data,
        credentials: 'same-origin', // only send cookies to the same origin
        redirect: 'follow',         // follows site redirection
        mode: 'same-origin',        // requisition for same site origin
        cache: 'default'
    };

    try {
        const response = await fetch(url, init);
        if (!response.ok) {
            // Fetch completed but received a http error code from server
            console.log(response);
        } else if (response.redirected) {
            // Fetch completed with a redirection
            html = await response.text();
            document.documentElement.innerHTML = html;
        }
    } catch (error) {
        // The fetch couldn't complete
        console.log(error);
    }
}


// Add a form submission event listener and prevent the normal form submission
// process.
function formSubmissionEvent() {
    $('form').submit(function(event) {
        sendFormData();
        // Stop the form from submitting the normal way and refreshing the page
        event.preventDefault();
    });
}


// Attach the listener to the form only when the page finished loading.
$(document).ready(function() {
    // Send form data through submission event listener
    formSubmissionEvent();
});
