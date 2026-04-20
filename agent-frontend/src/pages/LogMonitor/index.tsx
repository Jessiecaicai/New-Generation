import React, { useState, useEffect, useCallback } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Select,
  Statistic,
  Row,
  Col,
  Modal,
  message,
  Typography,
  Badge,
} from 'antd';
import {
  ReloadOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  BugOutlined,
} from '@ant-design/icons';
import { getLogs, getLogStats, resolveLog, getLogContext } from '@/services/logService';

const { Paragraph } = Typography;

const LogMonitorPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [levelFilter, setLevelFilter] = useState<string | undefined>(undefined);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [contextModal, setContextModal] = useState<{ open: boolean; data: any }>({
    open: false,
    data: null,
  });

  const fetchStats = useCallback(async () => {
    try {
      const data = await getLogStats(24);
      setStats(data);
    } catch { /* ignore */ }
  }, []);

  const fetchLogs = useCallback(
    async (page = 1) => {
      setLoading(true);
      try {
        const data = await getLogs({
          level: levelFilter,
          page: page - 1,
          size: pagination.pageSize,
        });
        setLogs(data.content || []);
        setPagination((prev) => ({ ...prev, current: page, total: data.totalElements || 0 }));
      } catch {
        message.error('获取日志失败');
      } finally {
        setLoading(false);
      }
    },
    [levelFilter, pagination.pageSize],
  );

  useEffect(() => {
    fetchStats();
    fetchLogs();
  }, [fetchStats, fetchLogs]);

  // Auto refresh every 30s
  useEffect(() => {
    const timer = setInterval(() => {
      fetchStats();
      fetchLogs(pagination.current);
    }, 30000);
    return () => clearInterval(timer);
  }, [fetchStats, fetchLogs, pagination.current]);

  const handleResolve = async (id: number) => {
    try {
      await resolveLog(id);
      message.success('已标记为已处理');
      fetchLogs(pagination.current);
      fetchStats();
    } catch {
      message.error('操作失败');
    }
  };

  const handleViewContext = async (id: number) => {
    try {
      const data = await getLogContext(id);
      setContextModal({ open: true, data });
    } catch {
      message.error('获取上下文失败');
    }
  };

  const levelConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    INFO: { color: 'blue', icon: <CheckCircleOutlined /> },
    WARN: { color: 'orange', icon: <WarningOutlined /> },
    ERROR: { color: 'red', icon: <CloseCircleOutlined /> },
    FATAL: { color: '#cf1322', icon: <BugOutlined /> },
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 180,
      render: (val: string) => val?.replace('T', ' ').substring(0, 19),
    },
    {
      title: '级别',
      dataIndex: 'logLevel',
      key: 'logLevel',
      width: 90,
      render: (level: string) => {
        const cfg = levelConfig[level] || { color: 'default', icon: null };
        return (
          <Tag color={cfg.color} icon={cfg.icon}>
            {level}
          </Tag>
        );
      },
    },
    {
      title: '服务',
      dataIndex: 'serviceName',
      key: 'serviceName',
      width: 140,
      render: (val: string) => (
        <Tag>{val === 'JAVA_BACKEND' ? 'Java 后端' : 'Python Agent'}</Tag>
      ),
    },
    { title: '分类', dataIndex: 'category', key: 'category', width: 140, ellipsis: true },
    { title: '消息', dataIndex: 'message', key: 'message', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'isResolved',
      key: 'isResolved',
      width: 80,
      render: (resolved: boolean) =>
        resolved ? (
          <Badge status="success" text="已处理" />
        ) : (
          <Badge status="error" text="未处理" />
        ),
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleViewContext(record.id)}>
            上下文
          </Button>
          {!record.isResolved && (
            <Button type="link" size="small" onClick={() => handleResolve(record.id)}>
              标记处理
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <PageContainer title="日志监控" subTitle="系统异常日志实时监控">
      {/* Stats */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="ERROR (24h)"
              value={stats.errorCount || 0}
              valueStyle={{ color: '#cf1322' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="WARN (24h)"
              value={stats.warnCount || 0}
              valueStyle={{ color: '#faad14' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="未处理异常"
              value={stats.unresolvedCount || 0}
              valueStyle={{ color: stats.unresolvedCount > 0 ? '#cf1322' : '#3f8600' }}
              prefix={<BugOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="分类数" value={Object.keys(stats.categoryStats || {}).length} />
          </Card>
        </Col>
      </Row>

      {/* Table */}
      <Card
        title="日志列表"
        extra={
          <Space>
            <Select
              placeholder="日志级别"
              allowClear
              style={{ width: 120 }}
              value={levelFilter}
              onChange={(val) => setLevelFilter(val)}
              options={[
                { label: '全部', value: undefined },
                { label: 'INFO', value: 'INFO' },
                { label: 'WARN', value: 'WARN' },
                { label: 'ERROR', value: 'ERROR' },
                { label: 'FATAL', value: 'FATAL' },
              ]}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                fetchStats();
                fetchLogs(1);
              }}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showTotal: (t) => `共 ${t} 条日志`,
            showSizeChanger: false,
            onChange: (page) => fetchLogs(page),
          }}
          rowClassName={(record) =>
            !record.isResolved && (record.logLevel === 'ERROR' || record.logLevel === 'FATAL')
              ? 'error-row'
              : ''
          }
        />
      </Card>

      {/* Context Modal */}
      <Modal
        title="日志上下文"
        open={contextModal.open}
        onCancel={() => setContextModal({ open: false, data: null })}
        footer={null}
        width={800}
      >
        {contextModal.data && (
          <div>
            {(Array.isArray(contextModal.data) ? contextModal.data : [contextModal.data]).map(
              (log: any, idx: number) => (
                <div
                  key={idx}
                  style={{
                    padding: '8px 12px',
                    marginBottom: 4,
                    backgroundColor:
                      log.logLevel === 'ERROR' || log.logLevel === 'FATAL' ? '#fff2f0' : '#fafafa',
                    borderRadius: 4,
                    fontSize: 13,
                    fontFamily: 'monospace',
                  }}
                >
                  <Tag
                    color={levelConfig[log.logLevel]?.color || 'default'}
                    style={{ marginRight: 8 }}
                  >
                    {log.logLevel}
                  </Tag>
                  <span style={{ color: '#999', marginRight: 8 }}>
                    {log.createdAt?.replace('T', ' ').substring(0, 19)}
                  </span>
                  <span>{log.message}</span>
                  {log.stackTrace && (
                    <Paragraph
                      code
                      style={{ marginTop: 4, fontSize: 12, whiteSpace: 'pre-wrap' }}
                      ellipsis={{ rows: 5, expandable: true }}
                    >
                      {log.stackTrace}
                    </Paragraph>
                  )}
                </div>
              ),
            )}
          </div>
        )}
      </Modal>
    </PageContainer>
  );
};

export default LogMonitorPage;
