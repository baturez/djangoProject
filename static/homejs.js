function toggleComments(postId) {
    const commentsSection = document.getElementById('comments-' + postId);
    commentsSection.style.display = commentsSection.style.display === 'none' ? 'block' : 'none';
}

function submitComment(event, postId) {
    event.preventDefault();

    const form = event.target;
    const commentContent = form.comment_content.value;

    fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            post_id: postId,
            comment_content: commentContent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const commentsSection = document.getElementById('comments-' + postId);

            commentsSection.insertAdjacentHTML('beforeend', `
                <div class="comment">
                    <strong>${data.commenter}</strong>: ${data.comment_content}
                    <small>${new Date().toLocaleString()}</small>
                </div>
            `);

            form.reset();
        } else {
            alert(data.error_message || 'Failed to add comment.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while adding your comment.');
    });
}



let chatSocket = null;
let selectedFriend = null;
let notificationButton = document.querySelector('.toggle-chat-btn');

function selectFriend(friendUsername) {
    selectedFriend = friendUsername;
    document.getElementById("selected-friend-name").textContent = `Sohbet - ${friendUsername}`;
    document.getElementById("chat-section").style.display = "block";

    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML = "";

    if (chatSocket) chatSocket.close();

    const yourUsername = getUsernameFromSession();
    const groupName = `chat_${[yourUsername, selectedFriend].sort().join('_')}`;


    chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${groupName}/`);

    chatSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        displayMessage(data);
    };

    chatSocket.onclose = function () {
        console.error("WebSocket connection closed.");
    };

    fetchMessages(friendUsername, chatMessages);
    markMessagesAsRead(yourUsername, friendUsername);
}
function markMessagesAsRead(sender, recipient) {
    fetch(`/mark_messages_as_read/${sender}/${recipient}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ sender: sender, recipient: recipient })
});
}

function displayMessage(data) {
    const chatMessages = document.getElementById("chat-messages");
    const messageElement = document.createElement("div");
    messageElement.className = "message";

    const senderElement = document.createElement("strong");
    const yourUsername = getUsernameFromSession();

    if (data.sender === yourUsername) {
        senderElement.textContent = `You: `;
        senderElement.classList.add("sender");
    } else {
        senderElement.textContent = `${data.sender}: `;
        senderElement.classList.add("receiver");
    }

    messageElement.appendChild(senderElement);
    const messageText = document.createElement("span");
    messageText.textContent = data.message || '';
    messageElement.appendChild(messageText);

    if (data.file_name && data.file_data) {
        addFileToMessage(messageElement, data);
    }

    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    if (selectedFriend !== data.sender) {
        notificationButton.classList.add("new-message");
        notificationButton.textContent = "🔔 Yeni Mesaj";
    }
}
document.addEventListener('DOMContentLoaded', function () {


    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (data.type === 'message') {
            const indicator = document.getElementById('new-message-indicator');
            if (indicator) {
                indicator.style.display = 'inline';
            }
        }
    };

    chatSocket.onclose = function (e) {
        console.error('Chat socket kapandı.');
    };

    window.clearNewMessageNotification = function () {
        const indicator = document.getElementById('new-message-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    };
});
function checkNewMessages() {
    fetch('/check-new-messages/')
        .then(response => {
            console.log('Response:', response);
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(`Server error: ${errorData.error}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Data:', data);
            if (data.new_message) {
                document.getElementById("new-message-indicator").style.display = "inline-block";
            }
        })
        .catch(error => console.error('Error checking new messages:', error));
}

setInterval(checkNewMessages, 10000);
function clearNewMessageNotification() {
    const notificationIndicator = document.getElementById('new-message-indicator');
    notificationIndicator.style.display = 'none';
}




function getUsernameFromSession() {
    return document.getElementById("username").dataset.username;
}
function reconnectWebSocket() {
    const newUsername = getUsernameFromSession();
    if (selectedFriend) {
        const groupName = `chat_${[newUsername, selectedFriend].sort().join('_')}`;
        chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${groupName}/`);
        chatSocket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            displayMessage(data);
        };
    }
}
window.addEventListener('load', function () {
    const newUsername = getUsernameFromSession();
    if (newUsername) {
        reconnectWebSocket();
    }
});
chatSocket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    displayMessage(data);
};

function addFileToMessage(messageElement, data) {
    const fileData = data.file_data;
    const fileName = data.file_name;
    const fileSize = (data.file_size / 1024).toFixed(2);
    const fileInfoText = `Dosya: ${fileName} (${fileSize} KB)`;

    const downloadButton = document.createElement("button");
    downloadButton.textContent = "İndir";
    downloadButton.classList.add("btn", "btn-success", "btn-sm");
    downloadButton.style.marginLeft = "10px";

    downloadButton.onclick = function () {
        const link = document.createElement("a");
        link.href = `data:application/octet-stream;base64,${fileData}`;
        link.download = fileName;
        link.click();

        chatSocket.send(JSON.stringify({
            type: 'file_downloaded',
            file_name: fileName
        }));

        alert(`Dosya indirildi ve Silindi: ${fileName}`);
    };

    messageElement.appendChild(document.createTextNode(fileInfoText));
    messageElement.appendChild(downloadButton);
}





function fetchMessages(friendUsername, chatMessages) {
    fetch('/fetch_messages?friend=' + friendUsername)
    .then(response => response.json())
    .then(data => {
        if (data.messages) {
            chatMessages.innerHTML = '';

            data.messages.forEach(msg => {
                const messageElement = document.createElement("div");
                messageElement.className = "message";

                const senderElement = document.createElement("strong");

                const yourUsername = document.getElementById("username").dataset.username;

                if (msg.sender === yourUsername) {
                    senderElement.textContent = `You: `;
                    senderElement.classList.add("sender");
                } else {
                    senderElement.textContent = `${msg.sender}: `;
                    senderElement.classList.add("receiver");
                }

                messageElement.appendChild(senderElement);

                const messageText = document.createElement("span");
                messageText.textContent = msg.text || '';
                messageElement.appendChild(messageText);

                if (msg.file_name && msg.file_data) {
                    addFileToMessage(messageElement, msg);
                }

                chatMessages.appendChild(messageElement);
            });

            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    })
    .catch(error => console.error('Mesajları çekerken hata oluştu:', error));
}

function handleFileSelect(event) {
    const fileInput = event.target;
    const file = fileInput.files[0];

    if (file) {
        document.getElementById('file-name').innerText = file.name;
        document.getElementById('file-info').style.display = 'block';

        const progressBar = document.getElementById('progress-bar');
        progressBar.style.width = '0%';
        document.getElementById('upload-progress').style.display = 'block';
    }
}

function clearFile() {
    const fileInput = document.getElementById('file-input');
    fileInput.value = '';
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('upload-progress').style.display = 'none';
}

function simulateUploadProgress() {
    const progressBar = document.getElementById('progress-bar');
    let progress = 0;

    const interval = setInterval(() => {
        progress += 10;
        progressBar.style.width = `${progress}%`;

        if (progress >= 100) {
            clearInterval(interval);
            alert('Dosya başarıyla yüklendi!');
        }
    }, 300);
}
document.getElementById('file-input').addEventListener('change', () => {
    simulateUploadProgress();
});

function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const messageContent = messageInput.value.trim();
    const fileInput = document.getElementById("file-input");
    const file = fileInput.files[0];
    const yourUsername = document.getElementById("username").dataset.username;

    if ((messageContent || file) && chatSocket && selectedFriend) {
        const chatMessages = document.getElementById("chat-messages");
        const tempMessage = document.createElement("div");
        tempMessage.className = "message temp-message";
        tempMessage.textContent = "gönderiliyor...";
        chatMessages.appendChild(tempMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (file) {
            sendFileMessage(file, messageContent, yourUsername);
        } else {
            sendTextMessage(messageContent, yourUsername, tempMessage);
        }

        messageInput.value = "";
    } else {
        alert("Mesaj veya dosya göndermek için lütfen bir içerik seçin.");
    }
}

function sendTextMessage(messageContent, yourUsername, tempMessage) {
    try {
        chatSocket.send(JSON.stringify({
            message: messageContent,
            recipient: selectedFriend,
            sender: yourUsername
        }));

        chatSocket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.message) {
                tempMessage.remove();
                displayMessage(data);
            }
        };

    } catch (error) {
        console.error("Metin mesajı gönderme hatası:", error);
        alert("Mesaj gönderilemedi. Bağlantınızı kontrol edin.");
    }
}

function sendFileMessage(file, messageContent, yourUsername) {
    const fileReader = new FileReader();

    fileReader.onload = function (event) {
        const fileData = event.target.result.split(',')[1];

        chatSocket.send(JSON.stringify({
            message: messageContent || '',
            recipient: selectedFriend,
            sender: yourUsername,
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            fileData: fileData
        }));

        document.getElementById("file-input").value = "";
    };

    fileReader.readAsDataURL(file);
}











function toggleChat() {
    var chatBar = document.getElementById("chat-bar");
    var indicator = document.getElementById("new-message-indicator");
    var chatsection = document.getElementById("chat-section")
    if (chatBar.style.display === "none") {
        chatBar.style.display = "block";
        indicator.style.display = "none";
        chatsection.style.display = "none";
    } else {
        chatBar.style.display = "none";

        if (chatSocket) {
            chatSocket.close();
            chatSocket = null;
            console.log("WebSocket connection closed.");
        }
    }
}