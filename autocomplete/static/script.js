const input = document.getElementById('autocomplete-input');
const suggestions = document.getElementById('suggestions');
let currentIndex = -1;
let lastQuery = "";
let lastClickedKeyword = ""; // 暫存上一次點選的關鍵字
let isComposing = false; // 標記是否正在使用注音輸入法

function replaceCommonWord(originalText, suggestion) {
  if (!originalText || !suggestion) return suggestion;

  let modifiedOriginalText = originalText.trim();
  const prefix = "我想查詢";

  // 如果 suggestion 已經存在於 originalText 中，則不進行替換
  if (modifiedOriginalText.endsWith(suggestion)) {
    return modifiedOriginalText;
  }

  // 針對注音輸入法的處理
  if (isComposing) {
    // 注音輸入法下，不處理，等待 compositionend 事件
    return modifiedOriginalText;
  } else {
    // 非注音輸入法下，尋找最後一個空格後的文字進行替換
    const lastSpaceIndex = modifiedOriginalText.lastIndexOf(' ');
    if (lastSpaceIndex !== -1) {
      modifiedOriginalText = modifiedOriginalText.substring(0, lastSpaceIndex);
    }
  }

  return (modifiedOriginalText + " " + suggestion).trim();
}

input.addEventListener('keydown', handleKeyNavigation);

function debounce(func, delay) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      func.apply(this, args);
    }, delay);
  };
}

const debouncedHandleInput = debounce(function () {
  // 在非注音輸入狀態下才處理
  if (!isComposing) {
    const query = this.value.trim();
    lastClickedKeyword = ""; // 清除 lastClickedKeyword
    suggestions.innerHTML = '';
    currentIndex = -1;

    if (query) {
      const lastSpaceIndex = query.lastIndexOf(' ');
      const currentKeyword = lastSpaceIndex === -1 ? query : query.substring(lastSpaceIndex + 1);

      fetch(`http://127.0.0.1:5000/autocomplete?query=${encodeURIComponent(currentKeyword)}`)
        .then(response => response.json())
        .then(showSuggestions)
        .catch(error => {
          console.error("API 請求失敗:", error);
          suggestions.innerHTML = '<div class="error">無法加載建議。</div>';
        });
    }
    lastQuery = query;
  }
}, 250);

// 監聽 composition 事件
input.addEventListener('compositionstart', () => {
  isComposing = true;
});

input.addEventListener('compositionend', (event) => {
  isComposing = false;
  // 在 compositionend 後觸發 debouncedHandleInput
  debouncedHandleInput.call(input); // 使用 call 確保 this 指向 input
});

input.addEventListener('input', () => {
  // 如果正在注音輸入，則不立即觸發，等待 compositionend
  if (!isComposing) {
    debouncedHandleInput.call(input); // 使用 call 確保 this 指向 input
  }
});

function showSuggestions(data) {
  if (!data || data.length === 0) {
    suggestions.innerHTML = '<div class="no-suggestions">沒有相關建議。</div>';
    return;
  }
  data.forEach((keyword, index) => {
    const div = document.createElement('div');
    div.textContent = keyword;
    div.onclick = () => {
      lastClickedKeyword = keyword; // 更新 lastClickedKeyword
      input.value = replaceCommonWord(input.value, keyword);
      lastQuery = input.value;
      suggestions.innerHTML = '';
      input.focus();
    };
    suggestions.appendChild(div);
  });
}

function handleKeyNavigation(e) {
  const items = suggestions.children;
  if (!items.length) return;

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      currentIndex = (currentIndex + 1) % items.length;
      updateHighlight();
      break;
    case 'ArrowUp':
      e.preventDefault();
      currentIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1;
      updateHighlight();
      break;
    case 'Enter':
      if (currentIndex >= 0) {
        lastClickedKeyword = items[currentIndex].textContent; // 更新 lastClickedKeyword
        input.value = replaceCommonWord(input.value, items[currentIndex].textContent);
        lastQuery = input.value;
        suggestions.innerHTML = '';
        currentIndex = -1;
      }
      break;
  }
}

function updateHighlight() {
  const items = suggestions.children;
  Array.from(items).forEach((item, i) => {
    item.classList.toggle('highlighted', i === currentIndex);
    if (i === currentIndex) item.scrollIntoView({ block: 'nearest' });
  });
}

// 點擊空白處清空 suggestions
document.addEventListener('click', e => {
  if (!input.contains(e.target) && !suggestions.contains(e.target)) {
    suggestions.innerHTML = '';
    currentIndex = -1;
  }
});