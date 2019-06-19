// Load Google OAUTH 2 with the correct client ID
function loadGoogle(clientID) {
    gapi.load('auth2', function() {
        auth2 = gapi.auth2.init({
                client_id: clientID
                // Scopes to request in addition to 'profile' and 'email'
                // scope: 'additional_scope'
            });
    });
}


// Asynchronous send the Google access token to the server
async function sendGoogleToken(token) {
    // Google login button
    const gButton = $('#gSigninButton');
    // Server url
    let url = gButton.attr('url');
    // HTTP method
    let method = gButton.attr('method');

    let init = {
        method: method,
        body: token,
        redirect: 'follow',         // follows site redirection
        mode: 'cors',        // requisition for same site origin
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

// Oauth Google JSON response (authResult). If succeed the authorization code
// will be sent to server API endpoint.
function gSignInCallback(authResult) {
    if (authResult['code']) {
        let code = authResult['code'];
        sendGoogleToken(code);
    } else if (authResult['error']) {
        console.log('There was an error: ' + authResult['error']);
    }
}

// Google Login
function googleLogin() {
    auth2.grantOfflineAccess({'redirect_uri': 'postmessage'}).then(gSignInCallback);
}


// Load Facebook OAUTH 2 and SDK with the correct client ID
function loadFacebook(clientID) {
    window.fbAsyncInit = function() {
        FB.init({
            appId      : clientID,
            cookie     : true,    // enable cookies to allow the server to
                                  // access the session
            xfbml      : true,    // parse social plugins on this page
            version    : 'v3.2'   // The Graph API version to use for the call
        });
    };

    // Load the SDK asynchronously
    (function(d, s, id) {
        var js, fjs = d.getElementsByTagName(s)[0];
        if (d.getElementById(id)) {return;}
        js = d.createElement(s); js.id = id;
        js.src = "https://connect.facebook.net/en_US/sdk.js";
        fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));
}


// Asynchronous send the facebook access token to the server
async function sendFacebookToken(token) {
    // Facebook login button
    const fButton = $('#fSigninButton');
    // Server url
    let url = fButton.attr('url');
    // HTTP METHOD
    let method = fButton.attr('method');

    let init = {
        method: method,
        body: token,
        redirect: 'follow',         // follows site redirection
        mode: 'cors',        // requisition for same site origin
        cache: 'default'
    };

    try {
        const response = await fetch(url, init);
        if (!response.ok) {
            // Fetch completed but received a http error code from server
            console.log(response);
        } else if (response.redirected) {
            // Fetch completed with a redirection
            console.log(response);
            html = await response.text();
            document.documentElement.innerHTML = html;
        }
    } catch (error) {
        // The fetch couldn't complete
        console.log(error);
    }
}

// Facebook Login
function facebookLogin() {
    FB.getLoginStatus(function(response) {
        // The response object is returned with a status field that
        // lets the app know the current login status of the person.
        // Full docs on the response object can be found in the
        // documentation for FB.getLoginStatus().
        if (response.status === 'connected') {
            // Logged into your app and Facebook.
            let access_token = response.authResponse.accessToken;
            // Sent the token to the server
            FB.api('/me', sendFacebookToken(access_token));
        } else {
            // The person is not logged into your app or we are unable to tell.
            console.log('Please log into this app.');
        }
    });
}


// Add oauth button's listeners when the page finished loading.
$(document).ready(function() {
    // Add login callback method to Facebook
    $("#fSigninButton").attr("onlogin", "facebookLogin()");

    // Google login button click listener
    $("#gSigninButton").click(function() {
        googleLogin();
    });
});