import React, { useState, useRef, useEffect, useCallback } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Input, Button, Space, Spin, Alert, message } from 'antd';
import { SendOutlined, ClearOutlined } from '@ant-design/icons';
import { submitChat, getTaskResult } from '@/services/chatService';
import { getLogStats } from '@/services/logService';
import MessageBubble from './components/MessageBubble';
import SqlResultCard from './components/SqlResultCard';
import KnowledgeCard from './components/KnowledgeCard';

const { TextArea } = Input;

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
  sql?: string;
  queryResults?: { columns: string[]; rows: Record<string, any>[]; rowCount: number };
  ragSources?: { text: string; source: string; score: number }[];
  loading?: boolean;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [sessionId] = useState(() => crypto.randomUUID());
  const [errorCount, setErrorCount] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

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

      // Submit task
      const { taskId } = await submitChat({ question, sessionId, conversationHistory: history });
      setStatusText('AI 正在思考...');

      // Poll for result
      const poll = setInterval(async () => {
        try {
          const task = await getTaskResult(taskId);
          if (task.status === 'PROCESSING') {
            setStatusText('AI 正在分析您的问题...');
          } else if (task.status === 'QUEUED') {
            setStatusText(`排队中，前方还有 ${task.queuePosition || 0} 个查询...`);
          } else if (task.status === 'SUCCESS' && task.result) {
            clearInterval(poll);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsg.id
                  ? {
                      ...m,
                      content: task.result!.answer,
                      intent: task.result!.intent,
                      sql: task.result!.sql,
                      queryResults: task.result!.queryResults,
                      ragSources: task.result!.ragSources,
                      loading: false,
                    }
                  : m,
              ),
            );
            setLoading(false);
            setStatusText('');
          } else if (task.status === 'ERROR') {
            clearInterval(poll);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsg.id
                  ? { ...m, content: `错误: ${task.error || '未知错误'}`, loading: false }
                  : m,
              ),
            );
            setLoading(false);
            setStatusText('');
            message.error(task.error || '处理失败');
          }
        } catch (e) {
          clearInterval(poll);
          setLoading(false);
          setStatusText('');
        }
      }, 1500);

      // Timeout after 2 minutes
      setTimeout(() => {
        clearInterval(poll);
        if (loading) {
          setLoading(false);
          setStatusText('');
          message.warning('请求超时');
        }
      }, 120000);
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
                <SqlResultCard sql={msg.sql} queryResults={msg.queryResults} />
              )}
              {msg.ragSources && msg.ragSources.length > 0 && (
                <KnowledgeCard sources={msg.ragSources} />
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
              onClick={() => setMessages([])}
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
