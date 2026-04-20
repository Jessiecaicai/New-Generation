import { request } from '@umijs/max';

/** 知识库列表 */
export async function listKnowledgeBases() {
  return request<any[]>('/api/knowledge');
}

/** 创建知识库 */
export async function createKnowledgeBase(name: string, description?: string) {
  return request('/api/knowledge', {
    method: 'POST',
    params: { name, description },
  });
}

/** 上传文档到知识库 */
export async function uploadDocument(kbId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return request(`/api/knowledge/${kbId}/documents`, {
    method: 'POST',
    data: formData,
  });
}

/** 删除知识库 */
export async function deleteKnowledgeBase(id: string) {
  return request(`/api/knowledge/${id}`, { method: 'DELETE' });
}
