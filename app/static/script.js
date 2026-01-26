const chatContainer = document.getElementById('chat-container');
const queryInput = document.getElementById('query-input');

async function askQuestion(queryText = null) {
    const query = queryText || queryInput.value;
    if (!query) return;

    addMessage('Me', query, 'user');
    if (!queryText) queryInput.value = '';  // 자동 인사일 경우 입력창 초기화 생략

    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
            credentials: 'same-origin'
        });

        const data = await response.json();
        addMessage('Bot', data.answer, 'bot');
    } catch (error) {
        console.error('Error in askQuestion:', error);
        addMessage('Error', `Failed to get answer: ${error.message}`, 'error');
    }
}

function addMessage(sender, message, className) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${className}`;

    const avatar = document.createElement('img');
    avatar.className = 'avatar';
    avatar.src = className === 'user' ? '/static/me.png' :
                 className === 'bot' ? '/static/bot.png' : '';
    avatar.alt = className === 'user' ? 'User Avatar' :
                 className === 'bot' ? 'Bot Avatar' : 'Default Avatar';

    const textElement = document.createElement('div');
    textElement.className = 'text';

    if (className === 'bot') {
        // 👉 마크다운 파싱
        let parsed = marked.parse(message);

        // 👉 링크가 새 창에서 열리도록 처리
        parsed = parsed.replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" ');

        textElement.innerHTML = `<strong>${sender}:</strong> ${parsed}`;
    } else {
        textElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    }

    messageElement.appendChild(avatar);
    messageElement.appendChild(textElement);

    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ✅ Enter 키로 질문 전송
queryInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        askQuestion();
    }
});

// ✅ 모바일 터치 입력 대응
queryInput.addEventListener('touchstart', function() {
    queryInput.focus();
});

// ✅ 페이지 로드시 챗봇 인사
window.addEventListener('DOMContentLoaded', function() {
    addMessage(
        'Bot',
        '안녕하세요. 저는 부산광역시 감염병관리지원단에서 제공하는  "법정감염병 알아보기 챗봇"입니다. 저는 "법정감염병 알아보기" 기반으로 답변드리며, 개별 감염병에 대한 질문만 가능합니다.',
        'bot'
    );
});

window.open(
    '/static/popup.html',
    '_blank',
    'width=680,height=600,noopener,noreferrer'
  );
  