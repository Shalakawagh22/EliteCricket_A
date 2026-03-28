function sendMessage(){

let message = document.getElementById("message").value
let chatbox = document.getElementById("chatbox")

chatbox.innerHTML += "<p><b>You:</b> " + message + "</p>"

fetch("/ask_ai",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({message:message})

})

.then(res => res.json())

.then(data => {

chatbox.innerHTML += "<p><b>AI Coach:</b> " + data.reply + "</p>"

})

document.getElementById("message").value=""

}
