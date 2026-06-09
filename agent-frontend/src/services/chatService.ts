import { request } from '@umijs/max';

/**
 * 同步提交聊天 —— 直接返回最终结果
 * （简化版：去掉任务队列和轮询机制）
 */
export async function submitChat(data: {
  question: string;
  sessionId?: string;
  conversationHistory?: { role: string; content: string }[];
  intentHint?: string;
}) {
  return request<{
    answer: string;
    intent: string;
    sql?: string;
    displaySql?: string;
    queryResults?: { columns: string[]; rows: Record<string, any>[]; rowCount: number };
    confidence?: number;
  }>('/api/chat', { method: 'POST', data });
}

/** 获取数据库 Schema */
export async function getSchema() {
  return request('/api/schema');
}
