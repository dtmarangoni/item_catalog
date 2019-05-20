// Loading Google OAUTH 2 with the correct client ID
function loadGoogle(clientID) {
    gapi.load('auth2', function() {
        auth2 = gapi.auth2.init({
                client_id: clientID
                // Scopes to request in addition to 'profile' and 'email'
                // scope: 'additional_scope'
            });
    });
}

// Oauth Google JSON response. If succeed the authorization code will be sent
// to server API endpoint.
function gSignInCallback(json) {
    authResult = json;
    if (authResult['code']) {
        $.ajax({
        type: 'POST',
        url: '/catalog/oauth_login/google',
        processData: false,
        data: authResult['code'],
        contentType: 'application/octet-stream; charset=utf-8',
        success: function(result) {
            // Handle or verify the server response if necessary.
            if (result) {
                window.location.href = "/catalog";
            } else {
                console.log('Failed to make a server-side call. Check your configuration and console.');
            }
        }
        });
    } else if (authResult['error']) {
        console.log('There was an error: ' + authResult['error']);
    }
}

// Google Login
function googleLogin() {
    auth2.grantOfflineAccess({'redirect_uri': 'postmessage'}).then(gSignInCallback);
}


// Loading Facebook OAUTH 2 and SDK with the correct client ID
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

// Facebook Login
function facebookLogin() {
    FB.getLoginStatus(function(response) {
        // The response object is returned with a status field that
        // lets the app know the current login status of the person.
        // Full docs on the response object can be found in the
        // documentation for FB.getLoginStatus().
        if (response.status === 'connected') {
            // Logged into your app and Facebook.
            var access_token = response.authResponse.accessToken;

            FB.api('/me', function(response) {
                $.ajax({
                    type: 'POST',
                    url: '/catalog/oauth_login/facebook',
                    processData: false,
                    data: access_token,
                    contentType: 'application/octet-stream; charset=utf-8',
                    success: function(result) {
                        // Handle or verify the server response if necessary.
                        if (result) {
                            window.location.href = "/catalog";
                        } else {
                            console.log('Failed to make a server-side call. Check your configuration and console.');
                        }
                    }
                });
            });
        } else {
            // The person is not logged into your app or we are unable to tell.
            document.getElementById('status').innerHTML = 'Please log into this app.';
        }
    });
}
