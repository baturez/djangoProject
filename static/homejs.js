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

function displayMessage(data) {
    const chatMessages = document.getElementById("chat-messages");

    // Yeni mesaj elementini oluştur
    const messageElement = document.createElement("div");
    messageElement.className = "message";

    // Gönderenin ismini mavi yapalım (Eğer mesajı biz göndermişsek)
    const senderElement = document.createElement("strong");

    const yourUsername = document.getElementById("username").dataset.username; // Kullanıcının ismini al

    if (data.sender === yourUsername) {
        // Eğer bu mesaj senin gönderdiğin bir mesaj ise
        senderElement.textContent = `You: `;
        senderElement.classList.add("sender"); // Kendi ismini mavi yapmak için
    } else {
        // Eğer mesaj karşı taraftan geldiyse
        senderElement.textContent = `${data.sender}: `;
        senderElement.classList.add("receiver"); // Karşıdaki göndereni yeşil yapmak için
    }

    messageElement.appendChild(senderElement);

    // Mesajın metnini ekleyelim
    const messageText = document.createElement("span");
    messageText.textContent = data.message || '';
    messageElement.appendChild(messageText);

    // Eğer mesajda dosya varsa, dosya ekle
    if (data.file_name && data.file_data) {
        addFileToMessage(messageElement, data);
    }

    // Yeni mesajı ekle
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;  // Otomatik kaydır
}

// WebSocket mesajı geldiğinde
chatSocket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    displayMessage(data); // Gelen mesajı ekle
};

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
    fetch('/fetch_messages?friend=' + friendUsername)
    .then(response => response.json())
    .then(data => {
        if (data.messages) {
            // Eski mesajları temizle
            chatMessages.innerHTML = '';

            // Mesajları tersten ekleyerek en alta ekleyelim
            data.messages.forEach(msg => {
                const messageElement = document.createElement("div");
                messageElement.className = "message";

                // Gönderenin ismini mavi yapalım (Eğer mesajı biz göndermişsek)
                const senderElement = document.createElement("strong");

                const yourUsername = document.getElementById("username").dataset.username; // Kullanıcının ismini al

                if (msg.sender === yourUsername) {
                    // Eğer bu mesaj senin gönderdiğin bir mesaj ise
                    senderElement.textContent = `You: `;
                    senderElement.classList.add("sender"); // Kendi ismini mavi yapmak için
                } else {
                    // Eğer mesaj karşı taraftan geldiyse
                    senderElement.textContent = `${msg.sender}: `;
                    senderElement.classList.add("receiver"); // Karşıdaki göndereni yeşil yapmak için
                }

                messageElement.appendChild(senderElement);

                // Mesajın metnini ekleyelim
                const messageText = document.createElement("span");
                messageText.textContent = msg.text || '';
                messageElement.appendChild(messageText);

                // Dosya varsa, dosyayı ekle
                if (msg.file_name && msg.file_data) {
                    addFileToMessage(messageElement, msg);
                }

                // Yeni mesajı en alta ekleyelim
                chatMessages.appendChild(messageElement);
            });

            // Mesajları ekledikten sonra, mesajı en altta tutmak için kaydırma
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
        // Geçici "gönderiliyor..." mesajını ekleme
        const chatMessages = document.getElementById("chat-messages");
        const tempMessage = document.createElement("div");
        tempMessage.className = "message temp-message";
        tempMessage.textContent = "gönderiliyor...";  // Geçici mesaj
        chatMessages.appendChild(tempMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;  // Otomatik kaydırma

        // WebSocket üzerinden mesaj gönderme
        if (file) {
            sendFileMessage(file, messageContent, yourUsername);
        } else {
            sendTextMessage(messageContent, yourUsername, tempMessage);
        }

        // Giriş alanlarını sıfırlama
        messageInput.value = "";
    } else {
        alert("Mesaj veya dosya göndermek için lütfen bir içerik seçin.");
    }
}

// Metin mesajı gönderme (dosya olmayan)
function sendTextMessage(messageContent, yourUsername, tempMessage) {
    try {
        chatSocket.send(JSON.stringify({
            message: messageContent,
            recipient: selectedFriend,
            sender: yourUsername
        }));

        // Gelen mesaj ile geçici mesajı güncelleme
        chatSocket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.message) {
                // Geçici mesajı kaldır, gerçek mesajı ekle
                tempMessage.remove();  // Geçici mesajı sil
                displayMessage(data);  // Gerçek mesajı ekle
            }
        };

    } catch (error) {
        console.error("Metin mesajı gönderme hatası:", error);
        alert("Mesaj gönderilemedi. Bağlantınızı kontrol edin.");
    }
}

// Dosya içeren mesaj gönderme
function sendFileMessage(file, messageContent, yourUsername) {
    const fileReader = new FileReader();

    fileReader.onload = function (event) {
        const fileData = event.target.result.split(',')[1];  // Base64 verisi

        // WebSocket üzerinden dosya mesajını gönder
        chatSocket.send(JSON.stringify({
            message: messageContent || '',
            recipient: selectedFriend,
            sender: yourUsername,
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            fileData: fileData
        }));

        // Dosya girişini sıfırla
        document.getElementById("file-input").value = "";  // Dosya seçimini sıfırla
    };

    fileReader.readAsDataURL(file);
}






// Mesajı kullanıcı arayüzünde göster




function toggleChat() {
    const chatBar = document.getElementById('chat-bar');
    const isVisible = chatBar.style.display === 'block';
    chatBar.style.display = isVisible ? 'none' : 'block';
}