

function toggleComments(postId) {
    const commentsSection = document.getElementById('comments-' + postId);
    commentsSection.style.display = commentsSection.style.display === 'none' ? 'block' : 'none';
}
function submitReply(event, postId, commentId) {
    event.preventDefault();
    const form = event.target;
    const replyContent = form.reply_content.value;

    fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            post_id: postId,
            comment_id: commentId,
            reply_content: replyContent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const commentDiv = form.closest('.comment');
            const repliesDiv = commentDiv.querySelector('.replies');
            repliesDiv.insertAdjacentHTML('beforeend', `
                <div class="reply">
                    <strong>${data.replier}</strong>: ${data.reply_content}
                    <small>${new Date().toLocaleString()}</small>
                </div>
            `);
            form.reset();
        } else {
            alert(data.error_message || 'Failed to add reply.');
        }
    });
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
    });
}

currentStoryIndex = 0;
stories = [
    'https://picsum.photos/200/300',
    'https://picsum.photos/200/300?1',
    'https://picsum.photos/200/300?2',
];

function showLargeStory(index) {
    currentStoryIndex = index;
    const largeStoryContainer = document.getElementById('largeStoryContainer');
    const largeStoryImage = document.getElementById('largeStoryImage');

    largeStoryImage.src = stories[currentStoryIndex];
    largeStoryContainer.style.display = 'flex';
}

function closeLargeStory() {
    const largeStoryContainer = document.getElementById('largeStoryContainer');
    largeStoryContainer.style.display = 'none';
}

function nextStory(event) {
    event.stopPropagation();
    currentStoryIndex++;
    if (currentStoryIndex >= stories.length) {
        currentStoryIndex = 0;
    }
    const largeStoryImage = document.getElementById('largeStoryImage');
    largeStoryImage.src = stories[currentStoryIndex];
}


let chatSocket = null;
let selectedFriend = null;

// Arkadaş seçimi işlevi
function selectFriend(friendUsername) {
    selectedFriend = friendUsername;
    document.getElementById("selected-friend-name").textContent = `Sohbet - ${friendUsername}`;
    document.getElementById("chat-section").style.display = "block";

    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML = "";  // Eski mesajları temizle

    if (chatSocket) chatSocket.close();  // Önceki WebSocket bağlantısını kapat

    const yourUsername = document.getElementById("username").dataset.username;
    const groupName = `chat_${[yourUsername, selectedFriend].sort().join('_')}`;

    // WebSocket bağlantısı kur
    chatSocket = new WebSocket(`wss://${window.location.host}/ws/chat/${groupName}/`);

    // Mesaj alma işlevi
    chatSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        displayMessage(data);
    };

    chatSocket.onclose = function () {
        console.error("WebSocket bağlantısı kapandı.");
    };

    fetchMessages(friendUsername, chatMessages);
}

// Mesajları görüntüleme işlevi
function displayMessage(data) {
    const chatMessages = document.getElementById("chat-messages");
    const messageElement = document.createElement("div");
    messageElement.className = "message";

    const messageText = `${data.sender}: ${data.message || ''}`;
    messageElement.textContent = messageText;

    if (data.file_name && data.file_data) {
        addFileToMessage(messageElement, data);
    }

    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;  // Otomatik kaydır
}

// Dosya bilgilerini mesaja ekle
function addFileToMessage(messageElement, data) {
    const fileData = data.file_data;  // Hata kaynağı düzeltiliyor
    const fileName = data.file_name;
    const fileSize = (data.file_size / 1024).toFixed(2);  // KB boyutu
    const fileInfoText = `Dosya: ${fileName} (${fileSize} KB)`;

    const downloadButton = document.createElement("button");
    downloadButton.textContent = "İndir";
    downloadButton.classList.add("btn", "btn-success", "btn-sm");
    downloadButton.style.marginLeft = "10px";

    downloadButton.onclick = function () {
        // Dosyayı indir
        const link = document.createElement("a");
        link.href = `data:application/octet-stream;base64,${fileData}`;
        link.download = fileName;
        link.click();  // Dosya indirme işlemini başlat

        // WebSocket üzerinden dosya indirildiğini bildiren mesaj gönder
        chatSocket.send(JSON.stringify({
            type: 'file_downloaded',
            file_name: fileName
        }));

        // Bildirim göster
        alert(`Dosya indirildi ve MongoDB'den silinmesi için işaretlendi: ${fileName}`);
    };

    messageElement.appendChild(document.createTextNode(fileInfoText));
    messageElement.appendChild(downloadButton);
}

// Dosya indirme bildirimini sunucuya gönder
function notifyFileDownloaded(fileName) {
    chatSocket.send(JSON.stringify({
        type: 'file_downloaded',
        file_name: fileName
    }));
}

// MongoDB'den mesajları çek
function fetchMessages(friendUsername, chatMessages) {
    fetch(`/fetch_messages?friend=${friendUsername}`)
        .then(response => response.json())
        .then(data => {
            if (data.messages) {
                data.messages.forEach(msg => {
                    const messageElement = document.createElement("div");
                    messageElement.className = "message";
                    messageElement.textContent = `${msg.sender}: ${msg.text}`;
                    chatMessages.appendChild(messageElement);
                });
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        })
        .catch(error => console.error('Mesajları çekerken hata oluştu:', error));
}

// Dosya seçimi işlevi
function handleFileSelect(event) {
    const fileInput = event.target;
    const file = fileInput.files[0];

    if (file) {
        document.getElementById("file-name").innerText = `Seçilen dosya: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
        document.getElementById("file-info").style.display = "block";
    }
}

// Dosya seçimini temizle
function clearFile() {
    const fileInput = document.getElementById("file-input");
    fileInput.value = "";  // Dosya girişini sıfırla
    document.getElementById("file-info").style.display = "none";  // Dosya bilgisini gizle
}

// Mesaj gönderme işlevi
function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const messageContent = messageInput.value.trim();
    const fileInput = document.getElementById("file-input");
    const file = fileInput.files[0];
    const yourUsername = document.getElementById("username").dataset.username;

    if ((messageContent || file) && chatSocket && selectedFriend) {
        if (file) {
            sendFileMessage(file, messageContent, yourUsername);
        } else {
            sendTextMessage(messageContent, yourUsername);
        }
        messageInput.value = "";  // Mesaj girişini temizle
    } else {
        alert("Mesaj veya dosya göndermek için lütfen bir içerik seçin.");
    }
}

// Dosya içeren mesaj gönderme
function sendFileMessage(file, messageContent, yourUsername) {
    const fileReader = new FileReader();

    fileReader.onload = function (event) {
        const fileData = event.target.result.split(',')[1];  // Base64 verisi

        chatSocket.send(JSON.stringify({
            message: messageContent || '',
            recipient: selectedFriend,
            sender: yourUsername,
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            fileData: fileData
        }));

        document.getElementById("file-input").value = "";  // Dosya girişini sıfırla
    };

    fileReader.readAsDataURL(file);
}

// Yalnızca metin mesajı gönder
function sendTextMessage(messageContent, yourUsername) {
    chatSocket.send(JSON.stringify({
        message: messageContent,
        recipient: selectedFriend,
        sender: yourUsername
    }));
}





// Mesajı kullanıcı arayüzünde göster




function toggleChat() {
    const chatBar = document.getElementById('chat-bar');
    const isVisible = chatBar.style.display === 'block';
    chatBar.style.display = isVisible ? 'none' : 'block';
}


