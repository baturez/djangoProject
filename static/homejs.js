

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

let currentStoryIndex = 0;
const stories = [
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

function selectFriend(friendUsername) {
    selectedFriend = friendUsername;
    document.getElementById("selected-friend-name").textContent = `Sohbet - ${friendUsername}`;
    document.getElementById("chat-section").style.display = "block";

    if (chatSocket) {
        chatSocket.close();
    }

    const yourUsername = document.getElementById("username").dataset.username;

    // Ortak grup adı oluşturuluyor (alfabetik sıralama için Math.min ve Math.max kullanılıyor)
    const groupName = `chat_${[yourUsername, selectedFriend].sort().join('_')}`;

    // WebSocket bağlantısını kurma
    chatSocket = new WebSocket(`wss://${window.location.host}/ws/chat/${groupName}/`);

    chatSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const chatMessages = document.getElementById("chat-messages");

        const messageElement = document.createElement("div");
        messageElement.className = "message";
        messageElement.textContent = `${data.sender}: ${data.message}`;
        chatMessages.appendChild(messageElement);

        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    chatSocket.onclose = function () {
        console.error("WebSocket bağlantısı kapandı.");
    };

    // MongoDB'den önceki mesajları çek
    fetch(`/fetch_messages?friend=${friendUsername}`)
        .then(response => response.json())
        .then(data => {
            const chatMessages = document.getElementById("chat-messages");
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
        .catch(error => console.error('Error fetching messages:', error));
}
// Dosya seçimi işlemi
function handleFileSelect(event) {
    const fileInput = event.target;
    const file = fileInput.files[0];

    if (file) {
        // Dosya adını ve boyutunu göster
        document.getElementById("file-name").innerText = `Seçilen dosya: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
        document.getElementById("file-info").style.display = "block";
    }
}

// Dosya kaldırma işlemi
function clearFile() {
    const fileInput = document.getElementById("file-input");
    fileInput.value = ""; // Dosya input'unu sıfırla
    document.getElementById("file-info").style.display = "none"; // Dosya bilgisini gizle
}

function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const messageContent = messageInput.value.trim();
    const fileInput = document.getElementById("file-input");
    const file = fileInput.files[0];
    const yourUsername = document.getElementById("username").dataset.username;

    if ((messageContent || file) && chatSocket && selectedFriend) {
        console.log('Sending message:', messageContent, 'to:', selectedFriend);  // Log the message and recipient

        // Eğer dosya varsa, dosya verisini base64 olarak okuyalım
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const fileData = event.target.result.split(',')[1];  // Base64 formatına dönüştür

                // WebSocket mesajını gönder
                chatSocket.send(JSON.stringify({
                    message: messageContent,  // Mesaj metni (boşsa null olabilir)
                    recipient: selectedFriend,
                    sender: yourUsername,
                    fileName: file.name,  // Dosya adı
                    fileSize: file.size,  // Dosya boyutu
                    fileData: fileData    // Base64 dosya verisi
                }));

                // Dosya yüklendikten sonra inputları sıfırla
                fileInput.value = "";  // Dosya inputunu sıfırla
            };
            reader.readAsDataURL(file);  // Dosyayı base64 formatında oku
        } else {
            // Sadece mesaj gönderiliyorsa, dosya olmadan
            chatSocket.send(JSON.stringify({
                message: messageContent,
                recipient: selectedFriend,
                sender: yourUsername
            }));
        }

        // Mesaj inputunu sıfırla
        messageInput.value = "";
    }
}



function toggleChat() {
    const chatBar = document.getElementById('chat-bar');
    const isVisible = chatBar.style.display === 'block';
    chatBar.style.display = isVisible ? 'none' : 'block';
}

document.getElementById('send-button').addEventListener('click', sendMessage);

