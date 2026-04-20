import { request } from '@umijs/max';

/** 查询日志列表 */
export async function getLogs(params: {
  level?: string;
  page?: number;
  size?: number;
}) {
  return request('/api/logs', { params });
}

/** 日志统计 */
export async function getLogStats(hours: number = 24) {
  return request<{
    errorCount: number;
    warnCount: number;
    unresolvedCount: number;
    categoryStats: Record<string, number>;
  }>('/api/logs/stats', { params: { hours } });
}

/** 获取日志上下文 */
export async function getLogContext(id: number) {
  return request(`/api/logs/${id}/context`);
}

/** 标记日志已处理 */
export async function resolveLog(id: number) {
  return request(`/api/logs/${id}/resolve`, { method: 'PUT' });
}
