import { request } from '@umijs/max';

/** 提交聊天（异步任务） */
export async function submitChat(data: {
  question: string;
  sessionId?: string;
  conversationHistory?: { role: string; content: string }[];
  knowledgeBases?: string[];
  intentHint?: string;
}) {
  return request<{ taskId: string; status: string; queuePosition?: number }>(
    '/api/chat',
    { method: 'POST', data },
  );
}

/** 轮询任务状态 */
export async function getTaskResult(taskId: string) {
  return request<{
    taskId: string;
    status: string;
    queuePosition?: number;
    result?: {
      answer: string;
      intent: string;
      sql?: string;
      queryResults?: { columns: string[]; rows: Record<string, any>[]; rowCount: number };
      ragSources?: { text: string; source: string; score: number }[];
      confidence?: number;
    };
    error?: string;
  }>(`/api/tasks/${taskId}`);
}

/** 获取数据库 Schema */
export async function getSchema() {
  return request('/api/schema');
}
