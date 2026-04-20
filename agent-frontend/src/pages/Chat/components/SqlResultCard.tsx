import React, { useState } from 'react';
import { Card, Table, Typography, Tag, Button } from 'antd';
import { CodeOutlined, TableOutlined, DownOutlined, UpOutlined } from '@ant-design/icons';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const { Text } = Typography;

interface SqlResultCardProps {
  sql: string;
  queryResults: {
    columns: string[];
    rows: Record<string, any>[];
    rowCount: number;
  };
}

const SqlResultCard: React.FC<SqlResultCardProps> = ({ sql, queryResults }) => {
  const [showSql, setShowSql] = useState(false);

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
          <div style={{ borderBottom: '1px solid #f0f0f0' }}>
            <SyntaxHighlighter
              language="sql"
              style={vs2015}
              customStyle={{
                margin: 0,
                padding: 12,
                fontSize: 13,
                borderRadius: 0,
              }}
            >
              {sql}
            </SyntaxHighlighter>
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
