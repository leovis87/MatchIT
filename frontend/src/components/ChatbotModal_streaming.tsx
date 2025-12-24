// ============================================================================
// 📌 ChatbotModal.tsx 수정 버전
// 마커 기반으로 영역별 다른 스타일 적용
// ============================================================================

// ChatbotModal.tsx
// 🔥 스트리밍 + Markdown + 영역별 스타일 지원 버전

import React, { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent, ChangeEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import './ChatbotModal.css';

// ==========================================
// 타입 정의
// ==========================================

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatRequest {
  message: string;
  user_id: string;
}

// ==========================================
// 🔥 마커 기반 콘텐츠 파싱 함수
// ==========================================

interface ParsedSection {
  type: 'ai-greeting' | 'job-cards' | 'bootcamp-cards' | 'ai-roadmap' | 'ai-closing' | 'plain';
  content: string;
}

const parseMessageContent = (content: string): ParsedSection[] => {
  const sections: ParsedSection[] = [];
  
  // 마커 패턴 정의
  const markers = [
    { start: '<!-- AI_GREETING -->', end: '<!-- /AI_GREETING -->', type: 'ai-greeting' as const },
    { start: '<!-- JOB_CARDS -->', end: '<!-- /JOB_CARDS -->', type: 'job-cards' as const },
    { start: '<!-- BOOTCAMP_CARDS -->', end: '<!-- /BOOTCAMP_CARDS -->', type: 'bootcamp-cards' as const },
    { start: '<!-- AI_ROADMAP -->', end: '<!-- /AI_ROADMAP -->', type: 'ai-roadmap' as const },
    { start: '<!-- AI_CLOSING -->', end: '<!-- /AI_CLOSING -->', type: 'ai-closing' as const },
  ];
  
  let remainingContent = content;
  let lastIndex = 0;
  
  // 정규식으로 모든 마커 찾기
  const allMarkers: { index: number; marker: typeof markers[0]; isStart: boolean }[] = [];
  
  markers.forEach(marker => {
    let startIdx = content.indexOf(marker.start);
    while (startIdx !== -1) {
      allMarkers.push({ index: startIdx, marker, isStart: true });
      startIdx = content.indexOf(marker.start, startIdx + 1);
    }
    
    let endIdx = content.indexOf(marker.end);
    while (endIdx !== -1) {
      allMarkers.push({ index: endIdx, marker, isStart: false });
      endIdx = content.indexOf(marker.end, endIdx + 1);
    }
  });
  
  // 인덱스 순으로 정렬
  allMarkers.sort((a, b) => a.index - b.index);
  
  let currentPos = 0;
  let currentMarker: typeof markers[0] | null = null;
  let sectionStart = 0;
  
  for (const item of allMarkers) {
    if (item.isStart) {
      // 시작 마커 전의 plain 텍스트
      if (item.index > currentPos) {
        const plainContent = content.slice(currentPos, item.index).trim();
        if (plainContent) {
          sections.push({ type: 'plain', content: plainContent });
        }
      }
      currentMarker = item.marker;
      sectionStart = item.index + item.marker.start.length;
    } else if (currentMarker && item.marker.type === currentMarker.type) {
      // 종료 마커 - 섹션 추출
      const sectionContent = content.slice(sectionStart, item.index).trim();
      if (sectionContent) {
        sections.push({ type: currentMarker.type, content: sectionContent });
      }
      currentPos = item.index + item.marker.end.length;
      currentMarker = null;
    }
  }
  
  // 남은 텍스트
  if (currentPos < content.length) {
    const remaining = content.slice(currentPos).trim();
    if (remaining) {
      sections.push({ type: 'plain', content: remaining });
    }
  }
  
  // 마커가 없으면 전체를 plain으로
  if (sections.length === 0 && content.trim()) {
    sections.push({ type: 'plain', content: content.trim() });
  }
  
  return sections;
};

// ==========================================
// 컴포넌트
// ==========================================

const ChatbotModal: React.FC = () => {
  // ==========================================
  // State 관리
  // ==========================================
  
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '안녕하세요! 👋\nMatchIT AI 채용 도우미예요.\n채용공고와 부트캠프를 찾아드릴게요!'
    }
  ]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // ==========================================
  // 자동 스크롤
  // ==========================================
  
  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // ==========================================
  // 🔥 스트리밍 메시지 전송
  // ==========================================
  
  const sendMessageStream = async (): Promise<void> => {
    if (!inputText.trim() || isLoading || isStreaming) return;
    
    const userMessage = inputText.trim();
    setInputText('');
    
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);
    
    setIsLoading(true);
    setIsStreaming(true);
    abortControllerRef.current = new AbortController();
    
    try {
      const requestBody: ChatRequest = {
        message: userMessage,
        user_id: '2'
      };
      
      const response = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      });
      
      if (!response.ok) throw new Error('API 요청 실패');
      if (!response.body) throw new Error('Response body is null');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      setIsLoading(false);
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const token = line.slice(6);
            if (token === '[DONE]') break;
            if (token.startsWith('[ERROR]')) throw new Error(token.slice(8));
            
            const processedToken = token.replace(/\\n/g, '\n');
            
            setMessages(prev => {
              const newMessages = [...prev];
              const lastIdx = newMessages.length - 1;
              newMessages[lastIdx] = {
                ...newMessages[lastIdx],
                content: newMessages[lastIdx].content + processedToken
              };
              return newMessages;
            });
          }
        }
      }
      
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            if (newMessages[lastIdx].content === '') {
              newMessages[lastIdx].content = '(응답이 취소되었습니다)';
            }
            return newMessages;
          });
        } else {
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              content: '죄송합니다. 오류가 발생했습니다.\n잠시 후 다시 시도해주세요.'
            };
            return newMessages;
          });
        }
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };
  
  const cancelStream = (): void => {
    abortControllerRef.current?.abort();
  };
  
  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessageStream();
    }
  };
  
  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>): void => {
    setInputText(e.target.value);
  };
  
  const handleClose = (): void => {
    cancelStream();
    setIsOpen(false);
  };
  
  const handleQuickQuestion = (question: string): void => {
    setInputText(question);
  };
  
  // ==========================================
  // 🔥 영역별 렌더링 함수
  // ==========================================
  
  const renderSection = (section: ParsedSection, key: number) => {
    const sectionClass = `message-section section-${section.type}`;
    const cleanContent = section.content
    .replace(/<!-- AI_GREETING -->/g, '')
    .replace(/<!-- \/AI_GREETING -->/g, '')
    .replace(/<!-- JOB_CARDS -->/g, '')
    .replace(/<!-- \/JOB_CARDS -->/g, '')
    .replace(/<!-- BOOTCAMP_CARDS -->/g, '')
    .replace(/<!-- \/BOOTCAMP_CARDS -->/g, '')
    .replace(/<!-- AI_ROADMAP -->/g, '')
    .replace(/<!-- \/AI_ROADMAP -->/g, '')
    .replace(/<!-- AI_CLOSING -->/g, '')
    .replace(/<!-- \/AI_CLOSING -->/g, '');
    
    return (
      <div key={key} className={sectionClass}>
        <ReactMarkdown
          components={{
            pre: ({ node, ...props }) => <div {...props} />,   // pre -> div
            code: ({ node, ...props }) => <span {...props} />, // code -> span
            a: ({ node, ...props }) => (
              <a 
                {...props} 
                target="_blank" 
                rel="noopener noreferrer"
                className="chat-link"
              />
            ),
            p: ({ node, ...props }) => <span {...props} />
          }}
        >
          {cleanContent}
        </ReactMarkdown>
      </div>
    );
  };
  
  // ==========================================
  // 렌더링
  // ==========================================
  
  return (
    <>
      <button 
        className="chatbot-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="챗봇 열기"
        type="button"
      >
        {isOpen ? '✕' : '💬'}
      </button>
      
      {isOpen && (
        <div className="chatbot-modal">
          <div className="chatbot-header">
            <div className="chatbot-title">
              <span className="chatbot-icon">🤖</span>
              <span>MatchIT AI</span>
              {isStreaming && (
                <span className="streaming-indicator">응답 중...</span>
              )}
            </div>
            <button 
              className="chatbot-close"
              onClick={handleClose}
              type="button"
            >
              ✕
            </button>
          </div>
          
          <div className="chatbot-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.role === 'assistant' ? (
                    <>
                      {/* 🔥 마커 기반으로 섹션 분리 후 렌더링 */}
                      {parseMessageContent(msg.content).map((section, sIdx) => 
                        renderSection(section, sIdx)
                      )}
                      {isStreaming && idx === messages.length - 1 && (
                        <span className="typing-cursor">▊</span>
                      )}
                    </>
                  ) : (
                    msg.content.split('\n').map((line, i, arr) => (
                      <React.Fragment key={i}>
                        {line}
                        {i < arr.length - 1 && <br />}
                      </React.Fragment>
                    ))
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && !isStreaming && (
              <div className="message assistant">
                <div className="message-content loading">
                  <span className="dot">.</span>
                  <span className="dot">.</span>
                  <span className="dot">.</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          <div className="chatbot-input">
            <textarea
              value={inputText}
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              disabled={isLoading || isStreaming}
              rows={1}
            />
            {isStreaming ? (
              <button 
                onClick={cancelStream}
                className="cancel-button"
                title="응답 중지"
                type="button"
              >
                ⏹
              </button>
            ) : (
              <button 
                onClick={sendMessageStream}
                disabled={!inputText.trim() || isLoading}
                className="send-button"
                type="button"
              >
                ➤
              </button>
            )}
          </div>
          
          {messages.length === 1 && (
            <div className="quick-questions">
              <button onClick={() => handleQuickQuestion('Python 개발자 채용 있어?')} type="button">
                🐍 Python 채용
              </button>
              <button onClick={() => handleQuickQuestion('신입 프론트엔드 개발자 추천해줘')} type="button">
                💻 신입 프론트엔드
              </button>
              <button onClick={() => handleQuickQuestion('React 배울 수 있는 부트캠프 찾아줘')} type="button">
                📚 React 부트캠프
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default ChatbotModal;
