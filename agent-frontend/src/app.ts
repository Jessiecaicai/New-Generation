import type { RunTimeLayoutConfig } from '@umijs/max';

// 全局初始状态
export async function getInitialState() {
  return {
    name: 'New-Generation',
    version: '1.0.0',
  };
}

// Pro Layout 运行时配置
export const layout: RunTimeLayoutConfig = () => {
  return {
    title: 'New-Generation',
    logo: false,
    menu: {
      locale: false,
    },
    layout: 'side',
    fixedHeader: true,
    fixSiderbar: true,
    contentWidth: 'Fluid',
    navTheme: 'light',
    colorPrimary: '#1890ff',
    footerRender: () => (
      null
    ),
  };
};
