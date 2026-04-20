import React from 'react';
import { Avatar, Spin, Typography } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ role, content, loading }) => {
  const isUser = role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        padding: '8px 16px',
        gap: 12,
      }}
    >
      <Avatar
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        style={{
          backgroundColor: isUser ? '#1890ff' : '#52c41a',
          flexShrink: 0,
        }}
      />
      <div
        style={{
          maxWidth: '70%',
          padding: '10px 16px',
          borderRadius: 12,
          backgroundColor: isUser ? '#e6f4ff' : '#f6ffed',
          border: `1px solid ${isUser ? '#91caff' : '#b7eb8f'}`,
          wordBreak: 'break-word',
        }}
      >
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#999' }}>
            <Spin size="small" />
            <span>AI 正在思考...</span>
          </div>
        ) : (
          <Paragraph
            style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}
          >
            {content}
          </Paragraph>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
