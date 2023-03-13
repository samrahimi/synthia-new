//Requires: core.js to be loaded first

window.state_dick = {}
window.model_zoo = []
const getModels = (cb) => {
    $.get("/models", (model_ids) => {
        window.model_zoo = []
        model_ids.forEach(async(m) => {
            var fullmodel = await fetch("/models/"+m)
            window.model_zoo.push(fullmodel)
            $("#model_id").append("<option value='"+m+"'>"+m+"</option>")
            if (typeof cb ==="function")
                cb(window.model_zoo)
        })
    })
}


const populateSessions = (activeSessionId) => {
    var sessions = window.state_dick.user.active_sessions
    if (activeSessionId)
        window.state_dick.active_session=activeSessionId
    else
        window.state_dick.active_session= sessions[0].SESSION_ID
    $(".chat-list ul").html("")
    sessions.forEach(session => { 
        session_li_template = `
        <li id="${session.SESSION_ID}" 
        class="session ${session.SESSION_ID == window.state_dick.active_session ? "active ": ""}" onclick="javascript:populateMessages('${session.SESSION_ID}');return false">
            <span class="icon"><img class="avatar_sm" src="/static/synthia.png" /></span>
            <span class="title">${session.ai_name}</span>
            <span class="time">Spawned From: ${session.model_id}</span>
        </li>`
        $(".chat-list ul").append(session_li_template)

    })
    console.log("attempt download models")
    getModels()
}

const populateMessages = (sessionId) =>{
    var sessions = window.state_dick.user.active_sessions
    var session = sessions.filter(x => x.SESSION_ID == sessionId)[0]
    window.state_dick.active_session = sessionId
    $(".session").removeClass("active")
    $("#"+sessionId).addClass("active")

    $("#chat-messages").html("")
    
    $("#chat-messages").append(`<p style="margin-left:10px">Session ID: ${session.SESSION_ID}. Context: chatting with ${session.ai_name}. Spawned from: <a href="/www/models/edit_model/${session.model_id}?user_id={{user.user_id}}">${session.model_id}</a></p>`)
    $("#chat-messages").append(`<p style="margin-left:10px">***BETA UPDATE*** Custom models are here!!! Create your own models, <a href="/models/create_model?user_id={{user.user_id}}">from scratch</a> or by customizing one of the <a href="/www/models?user_id={{user.user_id}}">existing models</a></p>`)
    if (session.useChatModel) {
        //Different schema than the Synthia protocol. 
        //TODO: update Synthia conversation schema to match the chat models
    } else {
    session.conversation.forEach(messagePair => {
        //Note: this needs to be refactored ASAP at the server...
        //the couplet pattern predicated on a mention of the sender within a string
        //is brittle as hell... yes its what the bot understands
        //but its exactly the opposite of a data structure you can work with
        var couplet=messagePair.split(session.ai_name+": ")
        couplet[0] = couplet[0].replace(session.user_name+": ", "")
        couplet[1] = couplet[1].replace(session.ai_name+": ", "")

        var synthiaAvatar="/static/synthia.png"

        var query= `<div class="message sent">
                                <span class="avatar"><img
                src="https://api.dicebear.com/5.x/shapes/svg?seed=${session.user_name}"
                alt="avatar"
                />
                </span>
            <span class="text"><sent-by>${session.user_name}</sent-by><br />${couplet[0]}</span>
        </div>
        `
        var reply=`<div class="message">
            <span class="avatar"><img src="${synthiaAvatar}" /></span>
            <span class="text"><sent-by>${session.ai_name}</sent-by><br />${couplet[1]}</span>
        </div>
        `

        var rendered_pair = query+reply
        $("#chat-messages").append(rendered_pair)
    })
}
let scrollDiv = document.querySelector("#chat-messages"); scrollDiv.scrollTop = scrollDiv.scrollHeight

}

const sendMessage=() =>		{
            //Step one: send your message to the bot
            var active = state_dick.active_session
            var sessions = window.state_dick.user.active_sessions
            var session = sessions.filter(x => x.SESSION_ID == active)[0]
            var q = $("#query-box").val()
            $("#query-box").attr("disabled", "disabled")
            var sent_message= `<div class="message sent">
                                <span class="avatar"><img
                    src="https://api.dicebear.com/5.x/shapes/svg?seed=${session.user_name}"
                    alt="avatar"
                    />
                    </span>
                <span class="text"><sent-by>${session.user_name}</sent-by><br />${q}</span>
            </div>
        `
            $("#chat-messages").append(sent_message)
            let scrollDiv = document.querySelector("#chat-messages"); scrollDiv.scrollTop = scrollDiv.scrollHeight

            var chatmsgref = $("#chat-messages")
            $.get("/sessions/"+active+"/query/"+encodeURIComponent(q), (response) =>{
                //Step two: display result
                var received_message=`<div class="message">
                    <span class="avatar"><img src="/static/synthia.png" /></span>
                    <span class="text"><sent-by>${session.ai_name}</sent-by><br />${response.response}</span>
                </div>
                `


                $("#chat-messages").append(received_message)

                //Step three: rinse and repeat - re-enable query box
                $("#query-box").removeAttr("disabled")
                $("#query-box").val("")
                
                //Step four: TODO - update state dick (but it shouldn't really matter because the DOM is holding the state)
                let scrollDiv = document.querySelector("#chat-messages"); scrollDiv.scrollTop = scrollDiv.scrollHeight
                // Create a Speech Synthesis Utterance 
                
                // Initialize the Web Speech API 
                let synth = window.speechSynthesis; 

                let utterance =new SpeechSynthesisUtterance(response.response); // Speak the text 
                synth.speak(utterance);
            })
        
        }

$(document).ready(function () {
    $("#spawn").on("click", (e) => {
        $("#popup").show()
        e.preventDefault()
    })

    $("#models").on("click", (e) => {
        location.href="/www/models?user_id="+$("#user_id").val()
        e.preventDefault
    })
    $("#create-model").on("click", (e) => {
        location.href="/www/create_model?user_id="+$("#user_id").val()
        e.preventDefault

    })
    $("#do_spawn").on("click", () => {
        http_post("/sessions/spawn", {"user_id":$("#user_id").val(), "model_id":$("#model_id").val(), "user_name": $("#user_name").val(), "ai_name": $("#ai_name").val()}, 
            (r) => {
                //we need to enforceLogin() ASAP
                $.get("/users/refresh/"+$("#user_id").val(), (u) =>{ 
                    $("#popup").hide()
                    window.state_dick={user:u}
                    populateSessions()
                    //populateMessages(window.state_dick.user.active_sessions[0].SESSION_ID)
                })
            }
        )
    })


    //we need to enforceLogin() ASAP
    $.get("/users/refresh/"+$("#user_id").val(), (u) =>{ 
        window.state_dick={user:u}
        populateSessions()
        populateMessages(window.state_dick.user.active_sessions[0].SESSION_ID)
    })

    document.addEventListener("keyup", function(event) {
    if (event.keyCode === 13) {
                sendMessage()
        }
    });

    /* No need to call this, because we included the JSON in the initial page load 
    refreshCurrentUser((user) => 
    {
        window.state_dick.user = user;
        populateSessions()
        //populateMessages()    
    })*/
    //$("#whatever").load("/static/components/mic.html")
})
