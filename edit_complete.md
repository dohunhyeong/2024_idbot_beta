# 웹 접근성 개선 완료 보고서

**프로젝트**: 법정감염병 알아보기 챗봇 (http://idbot.or.kr/)
**근거**: 웹와치(주) 정보통신접근성 품질인증 전문가 심사 보고서
**결과**: 미흡 4건 수정 완료 / 권고 1건 반영 완료

---

## 수정 완료 항목

### 항목 25 — 주로 사용하는 언어 명시 (필수)

**파일**: `app/templates/index.html` (line 2)

```html
<!-- Before -->
<html lang="en">

<!-- After -->
<html lang="ko">
```

---

### 항목 1 — 적절한 대체 텍스트 제공 (필수)

꾸밈용 이미지에 의미 없는 alt 텍스트가 있어 스크린리더가 불필요하게 읽는 문제 수정.
빈 alt 값(`alt=""`)으로 설정하여 스크린리더가 해당 이미지를 건너뛰도록 처리.

**파일 1**: `app/templates/index.html` (line 15)

```html
<!-- Before -->
<img src="/static/bot.png" alt="Icon" ...>

<!-- After -->
<img src="/static/bot.png" alt="" ...>
```

**파일 2**: `app/static/script.js` (line 37)

```javascript
// Before
avatar.alt = className === 'user' ? 'User Avatar' :
             className === 'bot' ? 'Bot Avatar' : 'Default Avatar';

// After
avatar.alt = '';
```

---

### 항목 26 — 사용자 요구에 따른 실행 (새 창 사전 알림) (필수)

링크 클릭 시 새 창이 열리기 전에 사용자에게 사전 안내가 없는 문제 수정.
`title="새창열림"` 속성을 추가하여 스크린리더 및 툴팁으로 새 창 열림을 사전 안내.

**파일**: `app/static/script.js` (line 47)

```javascript
// Before
parsed = parsed.replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" ');

// After
parsed = parsed.replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" title="새창열림" ');
```

---

### 항목 29 — 레이블 제공 (필수)

텍스트 입력창에 레이블이 없어 스크린리더 사용자가 입력 목적을 알 수 없는 문제 수정.
`<label>` 1:1 대응이 어려운 레이아웃이므로 `title` 속성으로 대체.

**파일**: `app/templates/index.html` (line 20)

```html
<!-- Before -->
<input type="text" id="query-input" placeholder="궁금하신 내용을 물어보세요!">

<!-- After -->
<input type="text" id="query-input" title="질문 입력" placeholder="궁금하신 내용을 물어보세요!">
```

---

### 항목 19 — aria-label 중복 텍스트 제거 (권고)

버튼의 `aria-label`에 "버튼"이라는 단어가 중복되어 스크린리더가 "전송 버튼 버튼"처럼 읽는 문제 수정.

**파일**: `app/templates/index.html` (lines 21, 23)

```html
<!-- Before -->
<button onclick="askQuestion()" aria-label="전송 버튼">전송</button>
<button onclick="endSession()" class="exit-button" aria-label="사용 종료 버튼">사용 종료</button>

<!-- After -->
<button onclick="askQuestion()" aria-label="전송">전송</button>
<button onclick="endSession()" class="exit-button" aria-label="사용 종료">사용 종료</button>
```

---

## 수정 파일 목록

| 파일 | 수정 항목 |
|------|-----------|
| `app/templates/index.html` | 항목 25, 항목 1, 항목 29, 항목 19 |
| `app/static/script.js` | 항목 1, 항목 26 |

---

## 검증 방법

1. **항목 25**: 브라우저 소스 보기에서 `<html lang="ko">` 확인
2. **항목 1**: macOS VoiceOver(`Cmd+F5`) 실행 후 아바타 이미지를 건너뜀 확인
3. **항목 26**: 챗봇 출처 링크에 마우스 호버 시 "새창열림" 툴팁 및 새 창 열림 확인
4. **항목 29**: VoiceOver로 입력창 포커스 시 "질문 입력" 읽힘 확인
5. **항목 19**: VoiceOver로 버튼 포커스 시 "전송 버튼" 대신 "전송"만 읽힘 확인
