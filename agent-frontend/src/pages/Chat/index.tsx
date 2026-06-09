import React, { useState, useRef, useEffect, useCallback } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Input, Button, Space, Spin, Alert, message } from 'antd';
import { SendOutlined, ClearOutlined } from '@ant-design/icons';
import { submitChat } from '@/services/chatService';
import { getLogStats } from '@/services/logService';
import MessageBubble from './components/MessageBubble';
import SqlResultCard from './components/SqlResultCard';

const { TextArea } = Input;

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
  sql?: string;
  displaySql?: string;
  queryResults?: { columns: string[]; rows: Record<string, any>[]; rowCount: number };
  loading?: boolean;
}

const MESSAGES_KEY = 'chat:messages';
const SESSION_KEY = 'chat:sessionId';

const loadMessages = (): ChatMessage[] => {
  try {
    const raw = localStorage.getItem(MESSAGES_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw) as ChatMessage[];
    // 清掉上次卸载时还卡在 loading 的气泡
    return arr.map((m) => ({ ...m, loading: false }));
  } catch {
    return [];
  }
};

const loadSessionId = (): string => {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  localStorage.setItem(SESSION_KEY, fresh);
  return fresh;
};

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [sessionId] = useState(loadSessionId);
  const [errorCount, setErrorCount] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages));
    } catch { /* quota or serialization issue – ignore */ }
  }, [messages]);

  // Scroll to bottom
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  // Poll log stats for alert bar
  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const stats = await getLogStats(1);
        setErrorCount(stats.unresolvedCount || 0);
      } catch { /* ignore */ }
    }, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleSend = useCallback(async () => {
    const question = inputValue.trim();
    if (!question || loading) return;

    // Add user message
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: question };
    const assistantMsg: ChatMessage = { id: crypto.randomUUID(), role: 'assistant', content: '', loading: true };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInputValue('');
    setLoading(true);
    setStatusText('正在提交...');

    try {
      // Build conversation history
      const history = messages
        .filter((m) => !m.loading)
        .map((m) => ({ role: m.role, content: m.content }));

      // 同步调用：直接 await 拿到最终结果（不再轮询）
      setStatusText('AI 正在思考...');
      const result = await submitChat({ question, sessionId, conversationHistory: history });
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsg.id
            ? {
                ...m,
                content: result.answer,
                intent: result.intent,
                sql: result.sql,
                displaySql: result.displaySql,
                queryResults: result.queryResults,
                loading: false,
              }
            : m,
        ),
      );
      setLoading(false);
      setStatusText('');
    } catch (e: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsg.id
            ? { ...m, content: `请求失败: ${e.message || '网络错误'}`, loading: false }
            : m,
        ),
      );
      setLoading(false);
      setStatusText('');
    }
  }, [inputValue, loading, messages, sessionId]);

  return (
    <PageContainer title={false}>
      <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
        {/* Alert bar */}
        {errorCount > 0 && (
          <Alert
            message={`系统有 ${errorCount} 条未处理的异常日志`}
            type="error"
            showIcon
            closable
            banner
            action={<a href="/logs">查看详情</a>}
            style={{ marginBottom: 8 }}
          />
        )}

        {/* Message list */}
        <div
          ref={listRef}
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '16px 0',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#999', marginTop: 100 }}>
              <h2>New-Generation 智能助手</h2>
              <p>试试输入：查询销售额前5的客户 / 最近有什么错误日志 / 帮我查一下知识库里的内容</p>
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id}>
              <MessageBubble role={msg.role} content={msg.content} loading={msg.loading} />
              {msg.sql && msg.queryResults && (
                <SqlResultCard
                  sql={msg.sql}
                  displaySql={msg.displaySql}
                  queryResults={msg.queryResults}
                />
              )}
            </div>
          ))}
        </div>

        {/* Status text */}
        {statusText && (
          <div style={{ padding: '4px 16px', color: '#1890ff', fontSize: 13 }}>
            <Spin size="small" /> {statusText}
          </div>
        )}

        {/* Input area */}
        <div style={{ padding: '12px 0', display: 'flex', gap: 8 }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="输入您的问题... (Enter 发送, Shift+Enter 换行)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <Space direction="vertical" size={4}>
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={loading}
            >
              发送
            </Button>
            <Button
              icon={<ClearOutlined />}
              onClick={() => {
                setMessages([]);
                // 清空时也重置 sessionId，开启新会话
                localStorage.removeItem(MESSAGES_KEY);
                localStorage.removeItem(SESSION_KEY);
              }}
              size="small"
              disabled={loading}
            >
              清空
            </Button>
          </Space>
        </div>
      </div>
    </PageContainer>
  );
};

export default ChatPage;
