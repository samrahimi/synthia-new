//uninspired javascript that might have got me a job 20 years ago
//meh. the way i see it, the user don't care whether his login get done in a redux SPA
//or if it's good old localStorage (an old school cookie-like thing)

//in fact this code does more than it seems, because the endpoints on the bank end
//return a user with a complete snapshot of their chats, chat messages, and instances
//the only thing it doesn't get is models for customization

//so once you're logged in, you just pick the session in the UI
//send a chat message, append UI with the response
//and call refreshCurrentUser so the state's still current if they navigate away and come back...
const http_post = (endpoint, payload, response_handler) => {
    console.log(JSON.stringify(payload))
    fetch(endpoint, {
        method: 'POST', // Specify the HTTP method
        body: JSON.stringify(payload),  // Collect form data
        contentType: "application/json"
    })
        .then(response => response.json()) // Read response as json
        .then(data => response_handler(data)) // run the callback 

}
const validateForm = (e) => {
    e.preventDefault();
            
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const passwordConfirmation = document.getElementById("password_confirmation").value.trim();
    const errorParagraph = document.querySelector(".error")
    if (!name || !email || !username || !password || !passwordConfirmation) {
        errorParagraph.innerText = "All fields are required.";
        errorParagraph.style.display = "block";
        return false;
    }

    if (/\s/.test(username)) {
        errorParagraph.innerText = "Username cannot contain spaces.";
        errorParagraph.style.display = "block";
        return false;
    }

    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        errorParagraph.innerText = "Please enter a valid email address.";
        errorParagraph.style.display = "block";
        return false;
    }

    if (password !== passwordConfirmation) {
        errorParagraph.innerText = "Passwords do not match.";
        errorParagraph.style.display = "block";
        return false;
    }

    errorParagraph.style.display = "none";
    return true

}

const http_get = (endpoint, response_handler) => {

    fetch(endpoint, {
        method:"GET",
        contentType:"application/json"
    })        .then(response => response.json()) // Read response as json
    .then(data => response_handler(data)) // run the callback 

    //$.getJSON(endpoint, response_handler)
}
function getComponent(container, componentUrl, callback) {
    $(container).load(componentUrl, callback)
}
function qs(key) { const queryString = window.location.search; const urlParams = new URLSearchParams(queryString); return urlParams.get(key); }
const isloggedin = () => {
    return localStorage.getItem("logged_in_user") !==null
}

const getCurrentUser = () => {
    return (localStorage.getItem("logged_in_user"))
}

const refreshCurrentUser = (hand_off_to) => {
    if (!isloggedin()) {
        console.log("no logged in user found, returning empty dictionary")
        return {}
    } else {
        http_get("/users/"+getCurrentUser().user_id, (updated_user_state) => 
        {
            localStorage["logged_in_user"]= updated_user_state
            if (typeof hand_off_to !== "undefined")
                hand_off_to(updated_user_state) //the caller may wish to wait before allowing operations on the state, thus the many splendored callbacks
        })
    }
}

$("form.login").on("submit", (e) => {
    login()
    return false
})

$("form.signup").on("submit", (e) => {
    if (validateForm(e))
        signup()
    e.preventDefault()
})

function refreshLogin(uid, callback) {
    http_post("/users/login", { "user_id": uid, "password": "", "refresh": True },
    (result) => {
        if (callback && typeof callback == "function") {
            callback(result)
        }
    })
}

function login() {
    $("input").attr("disabled", "disabled")
    http_post("/users/login", { "user_id": $("#username").val(), "password": $("#password").val() },
        function (result) {
            if (!result || typeof result === 'underfined') {
                $(".error").show()
                $("input").removeAttr("disabled")
            }
            else {
                localStorage["logged_in_user"] = JSON.stringify(result)
                console.log("persisting user in localstorage, login success")
                location.href = "/www/interactions/" + result.user_id
            }

        }
    )

}
function signup() {
    http_post("/users/signup", { "user_id": $("#username").val(), "password": $("#password").val(), "name": $("#username").val(), "email": "None" }, (result) => {
        if (!result || typeof result === 'undefined') {
            $(".error").show()
            $("input").removeAttr("disabled")
            return false
        }
    else
        {
            //window.parent.setUid(result.user_id)
            localStorage["logged_in_user"] = JSON.stringify(result)
            console.log("persisting user in localstorage, login success")
            location.href = "/www/interactions/"+result.user_id
        }
    })

}
function enforceLogin() {
    if (!isloggedin())
        location.href="/www/login"
}

$(document).ready(function () {


})