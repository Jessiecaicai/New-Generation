import React, { useState, useEffect, useCallback } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Card, List, Tag, Button, Modal, message, Typography, Space, Spin } from 'antd';
import { FileTextOutlined, EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import { getPrompts, reloadAgent } from '@/services/agentConfigService';

const { Paragraph, Text } = Typography;

interface PromptInfo {
  name: string;
  version: string;
  description: string;
}

const PromptManagePage: React.FC = () => {
  const [prompts, setPrompts] = useState<PromptInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewModal, setViewModal] = useState<{ open: boolean; prompt: PromptInfo | null }>({
    open: false,
    prompt: null,
  });

  const fetchPrompts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getPrompts();
      setPrompts(data.prompts || []);
    } catch {
      message.error('获取 Prompt 列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  const handleReload = async () => {
    try {
      await reloadAgent();
      message.success('Prompt 热加载成功');
      fetchPrompts();
    } catch {
      message.error('热加载失败');
    }
  };

  return (
    <PageContainer
      title="提示词管理"
      subTitle="查看和管理 Agent 的 Prompt 模板"
      extra={[
        <Button key="reload" type="primary" icon={<ReloadOutlined />} onClick={handleReload}>
          热加载
        </Button>,
      ]}
    >
      <Spin spinning={loading}>
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3, xl: 4 }}
          dataSource={prompts}
          renderItem={(prompt) => (
            <List.Item>
              <Card
                hoverable
                title={
                  <Space>
                    <FileTextOutlined style={{ color: '#1890ff' }} />
                    <span style={{ fontSize: 14 }}>{prompt.name}</span>
                  </Space>
                }
                extra={
                  <Tag color="blue">v{prompt.version}</Tag>
                }
                actions={[
                  <Button
                    key="view"
                    type="link"
                    icon={<EyeOutlined />}
                    onClick={() => setViewModal({ open: true, prompt })}
                  >
                    查看
                  </Button>,
                ]}
              >
                <Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  style={{ marginBottom: 0, minHeight: 44 }}
                >
                  {prompt.description || '暂无描述'}
                </Paragraph>
              </Card>
            </List.Item>
          )}
        />
      </Spin>

      {/* View Modal */}
      <Modal
        title={
          <Space>
            <FileTextOutlined />
            {viewModal.prompt?.name}
            {viewModal.prompt && <Tag color="blue">v{viewModal.prompt.version}</Tag>}
          </Space>
        }
        open={viewModal.open}
        onCancel={() => setViewModal({ open: false, prompt: null })}
        footer={null}
        width={700}
      >
        {viewModal.prompt && (
          <div>
            <Paragraph type="secondary">{viewModal.prompt.description}</Paragraph>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Prompt 模板存储在 YAML 文件中，可在 agent-python/app/prompts/templates/ 目录下直接编辑，
              编辑后点击"热加载"按钮即可生效。
            </Text>
          </div>
        )}
      </Modal>
    </PageContainer>
  );
};

export default PromptManagePage;
