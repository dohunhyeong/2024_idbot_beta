// const 로 변수 선언.
// document.getElementByID('chat-container') : document 라는 곳에서 chat-container 라는 ID를 기준으로 element를 불러올 거다~
const chatContainer = document.getElementById('chat-container');
const urlInput = document.getElementById('url-input');
const queryInput = document.getElementById('query-input');

//processURL 함수 선언 (javascript 에서의 함수 선언 : function)
async function processURL() {
    const url = urlInput.value; // 사용자가 url 을 입력하면은 해당 값을 value 라는 key 에다가 저장을 하는데 그것을 불러와서 url이라는 변수에 저장하겠다는 의미.
    if (!url) return;

    // 입력된 메시지를 찍어주도록 하는 함수.
    addMessage('System', 'Processing URL...', 'system');

    try {
        const response = await fetch('/process_url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to process URL');
        }
        
        const data = await response.json();
        addMessage('System', data.message, 'system');
    } catch (error) {
        console.error('Error in processURL:', error);
        addMessage('Error', `Failed to process URL: ${error.message}`, 'error');
    }
}

// 사용자의 질문을 처리하는 function 
// html 파트에 있는 query-input 이라는 id 를 가진 conatainer 에서 받은 입력값(사용자의 질문)을 받아서 queryInput으로서 맨 위에서 선언함.
// queryInput 의 value 값을 받아서 query 라는 변수에 담음.
async function askQuestion() {
    const query = queryInput.value;
    if (!query) return;

    addMessage('Me', query, 'user');
    queryInput.value = ''; //위에서 사용자가 질문을 했기 때문에, queryInput에 있는 값을 초기화 시켜줌.

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

/*
document.createElement('div') -> document 에 'div' 라는 태그를 만들거라는 의미. 그리고 'div' 태그 안에 들어가는 element 를 messageElement 로 봄.
messageElement.className 에다가 message classname 을 저장
messageElement.innerHTML 로 "sender : message 내용" 과 같은 형식으로 작성되도록 함.
chatContainer 에 messageElement를 추가
chatContainer에 scrollTop을 실행해서 가장 오래된 내용이 가장 위로 가도록 함.
*/
function addMessage(sender, message, className) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${className}`;
    messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Enter 키로 질문 제출
queryInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        askQuestion();
    }
});
