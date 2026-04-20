import React, { useState, useEffect, useCallback } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Card, List, Switch, Tag, Button, message, Space, Typography, Spin } from 'antd';
import {
  ThunderboltOutlined,
  ReloadOutlined,
  ApiOutlined,
  TagOutlined,
} from '@ant-design/icons';
import { getSkills, toggleSkill, reloadAgent } from '@/services/agentConfigService';

const { Text, Paragraph } = Typography;

interface Skill {
  name: string;
  description: string;
  enabled: boolean;
  intent_tags: string[];
  tools: string[];
}

const SkillManagePage: React.FC = () => {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [reloading, setReloading] = useState(false);

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getSkills();
      setSkills(data.skills || []);
    } catch {
      message.error('获取 Skill 列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const handleToggle = async (name: string, enabled: boolean) => {
    try {
      await toggleSkill(name, enabled);
      setSkills((prev) =>
        prev.map((s) => (s.name === name ? { ...s, enabled } : s)),
      );
      message.success(`${name} 已${enabled ? '启用' : '禁用'}`);
    } catch {
      message.error('操作失败');
      fetchSkills();
    }
  };

  const handleReload = async () => {
    setReloading(true);
    try {
      await reloadAgent();
      message.success('Agent 热加载成功');
      fetchSkills();
    } catch {
      message.error('热加载失败');
    } finally {
      setReloading(false);
    }
  };

  return (
    <PageContainer
      title="技能管理"
      subTitle="管理 Agent 的可插拔技能（Skill）"
      extra={[
        <Button
          key="reload"
          type="primary"
          icon={<ReloadOutlined />}
          loading={reloading}
          onClick={handleReload}
        >
          热加载 Agent
        </Button>,
      ]}
    >
      <Spin spinning={loading}>
        <List
          grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3 }}
          dataSource={skills}
          renderItem={(skill) => (
            <List.Item>
              <Card
                title={
                  <Space>
                    <ThunderboltOutlined style={{ color: skill.enabled ? '#1890ff' : '#d9d9d9' }} />
                    <span>{skill.name}</span>
                  </Space>
                }
                extra={
                  <Switch
                    checked={skill.enabled}
                    onChange={(checked) => handleToggle(skill.name, checked)}
                    checkedChildren="启用"
                    unCheckedChildren="禁用"
                  />
                }
                style={{
                  opacity: skill.enabled ? 1 : 0.6,
                  borderColor: skill.enabled ? '#1890ff' : '#d9d9d9',
                }}
              >
                <Paragraph type="secondary" style={{ marginBottom: 12 }}>
                  {skill.description}
                </Paragraph>

                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    <TagOutlined /> 意图标签：
                  </Text>
                  <div style={{ marginTop: 4 }}>
                    {skill.intent_tags.map((tag) => (
                      <Tag key={tag} color="blue">
                        {tag}
                      </Tag>
                    ))}
                  </div>
                </div>

                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    <ApiOutlined /> 工具列表：
                  </Text>
                  <div style={{ marginTop: 4 }}>
                    {skill.tools.map((tool) => (
                      <Tag key={tool} style={{ marginBottom: 4 }}>
                        {tool}
                      </Tag>
                    ))}
                  </div>
                </div>
              </Card>
            </List.Item>
          )}
        />
      </Spin>
    </PageContainer>
  );
};

export default SkillManagePage;
