function sendMessage(){

let message = document.getElementById("message").value;

fetch("/ask_ai",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
message:message
})
})
.then(res=>res.json())
.then(data=>{

let chatbox=document.getElementById("chatbox");

chatbox.innerHTML+=`
<div class="user-msg">${message}</div>
<div class="bot-msg">${data.reply}</div>
`;

document.getElementById("message").value="";

});


}
