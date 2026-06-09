import React, { useState } from 'react';
import { Card, Table, Typography, Tag, Button, Tabs, Tooltip, message } from 'antd';
import {
  CodeOutlined,
  TableOutlined,
  DownOutlined,
  UpOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const { Text } = Typography;

interface SqlResultCardProps {
  sql: string;                 // 标准 SQL（执行用）
  displaySql?: string;         // 直观 SQL（中文别名，可选）
  queryResults: {
    columns: string[];
    rows: Record<string, any>[];
    rowCount: number;
  };
}

const CodeBlock: React.FC<{ code: string }> = ({ code }) => {
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      message.success('SQL 已复制');
    } catch {
      message.error('复制失败');
    }
  };
  return (
    <div style={{ position: 'relative' }}>
      <Tooltip title="复制 SQL">
        <Button
          size="small"
          type="text"
          icon={<CopyOutlined />}
          onClick={onCopy}
          style={{
            position: 'absolute',
            top: 6,
            right: 8,
            zIndex: 1,
            color: '#bbb',
          }}
        />
      </Tooltip>
      <SyntaxHighlighter
        language="sql"
        style={vs2015}
        customStyle={{ margin: 0, padding: 12, fontSize: 13, borderRadius: 0 }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
};

const SqlResultCard: React.FC<SqlResultCardProps> = ({ sql, displaySql, queryResults }) => {
  const [showSql, setShowSql] = useState(true);

  const tableColumns = queryResults.columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    width: 150,
  }));

  const dataSource = queryResults.rows.map((row, idx) => ({
    ...row,
    _key: idx,
  }));

  // 如果两份 SQL 一样（或没返回 displaySql），就只显示一份
  const hasTwo = !!displaySql && displaySql.trim() !== sql.trim();

  return (
    <div style={{ padding: '0 60px', marginBottom: 8 }}>
      <Card
        size="small"
        title={
          <span>
            <TableOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            查询结果
            <Tag color="blue" style={{ marginLeft: 8 }}>
              {queryResults.rowCount} 条记录
            </Tag>
          </span>
        }
        extra={
          <Button
            type="link"
            size="small"
            icon={<CodeOutlined />}
            onClick={() => setShowSql(!showSql)}
          >
            {showSql ? <UpOutlined /> : <DownOutlined />} SQL
          </Button>
        }
        styles={{ body: { padding: 0 } }}
      >
        {showSql && (
          <div style={{ borderBottom: '1px solid #f0f0f0', background: '#1e1e1e' }}>
            {hasTwo ? (
              <Tabs
                size="small"
                defaultActiveKey="display"
                tabBarStyle={{ margin: 0, padding: '0 12px', background: '#2d2d2d' }}
                items={[
                  {
                    key: 'display',
                    label: <span style={{ color: '#fff' }}>直观 SQL（带中文别名）</span>,
                    children: <CodeBlock code={displaySql!} />,
                  },
                  {
                    key: 'standard',
                    label: <span style={{ color: '#fff' }}>标准 SQL（执行用）</span>,
                    children: <CodeBlock code={sql} />,
                  },
                ]}
              />
            ) : (
              <CodeBlock code={sql} />
            )}
          </div>
        )}
        <Table
          columns={tableColumns}
          dataSource={dataSource}
          rowKey="_key"
          size="small"
          scroll={{ x: 'max-content' }}
          pagination={
            dataSource.length > 10
              ? { pageSize: 10, size: 'small', showTotal: (t) => `共 ${t} 条` }
              : false
          }
        />
      </Card>
    </div>
  );
};

export default SqlResultCard;
