import { defineConfig } from '@umijs/max';

export default defineConfig({
  antd: {},
  access: {},
  model: {},
  initialState: {},
  request: {},
  layout: {
    title: 'New-Generation',
    locale: false,
  },
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
    },
  },
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      name: '智能对话',
      path: '/chat',
      component: './Chat',
      icon: 'MessageOutlined',
    },
    {
      name: '日志监控',
      path: '/logs',
      component: './LogMonitor',
      icon: 'AlertOutlined',
    },
    {
      name: 'Agent 配置',
      path: '/config',
      icon: 'SettingOutlined',
      routes: [
        {
          name: '技能管理',
          path: '/config/skills',
          component: './AgentConfig/SkillManage',
        },
        {
          name: '提示词管理',
          path: '/config/prompts',
          component: './AgentConfig/PromptManage',
        },
      ],
    },
  ],
  npmClient: 'npm',
});
