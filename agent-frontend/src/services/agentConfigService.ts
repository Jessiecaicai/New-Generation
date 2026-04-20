import { request } from '@umijs/max';

/** 获取所有 Skill 状态 */
export async function getSkills() {
  return request<{
    skills: {
      name: string;
      description: string;
      enabled: boolean;
      intent_tags: string[];
      tools: string[];
    }[];
  }>('/api/skills');
}

/** 启用/禁用 Skill */
export async function toggleSkill(name: string, enabled: boolean) {
  return request(`/api/skills/${name}/toggle`, {
    method: 'PUT',
    params: { enabled },
  });
}

/** 热加载 Agent（Skill + Prompt） */
export async function reloadAgent() {
  return request('/api/agent/reload', { method: 'POST' });
}

/** 获取 Prompt 模板列表 */
export async function getPrompts() {
  return request<{
    prompts: { name: string; version: string; description: string }[];
  }>('/api/prompts');
}
