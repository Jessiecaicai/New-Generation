import React, { useState } from 'react';
import { Card, List, Typography, Tag, Button } from 'antd';
import { BookOutlined, DownOutlined, UpOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface KnowledgeSource {
  text: string;
  source: string;
  score: number;
}

interface KnowledgeCardProps {
  sources: KnowledgeSource[];
}

const KnowledgeCard: React.FC<KnowledgeCardProps> = ({ sources }) => {
  const [expanded, setExpanded] = useState(false);

  const displaySources = expanded ? sources : sources.slice(0, 2);

  return (
    <div style={{ padding: '0 60px', marginBottom: 8 }}>
      <Card
        size="small"
        title={
          <span>
            <BookOutlined style={{ marginRight: 8, color: '#52c41a' }} />
            参考来源
            <Tag color="green" style={{ marginLeft: 8 }}>
              {sources.length} 条引用
            </Tag>
          </span>
        }
        extra={
          sources.length > 2 && (
            <Button type="link" size="small" onClick={() => setExpanded(!expanded)}>
              {expanded ? (
                <>
                  收起 <UpOutlined />
                </>
              ) : (
                <>
                  展开全部 <DownOutlined />
                </>
              )}
            </Button>
          )
        }
      >
        <List
          size="small"
          dataSource={displaySources}
          renderItem={(item, index) => (
            <List.Item style={{ padding: '8px 0' }}>
              <div style={{ width: '100%' }}>
                <div style={{ marginBottom: 4 }}>
                  <Tag color="default" style={{ marginRight: 8 }}>
                    #{index + 1}
                  </Tag>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {item.source}
                  </Text>
                  <Tag
                    color={item.score >= 0.8 ? 'green' : item.score >= 0.5 ? 'orange' : 'red'}
                    style={{ marginLeft: 8, fontSize: 11 }}
                  >
                    相关度 {(item.score * 100).toFixed(0)}%
                  </Tag>
                </div>
                <Paragraph
                  ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                  style={{ marginBottom: 0, fontSize: 13, color: '#555' }}
                >
                  {item.text}
                </Paragraph>
              </div>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default KnowledgeCard;
