import React, { useState, useEffect, useCallback } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Upload,
  message,
  Tag,
  Popconfirm,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  UploadOutlined,
  DeleteOutlined,
  DatabaseOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import {
  listKnowledgeBases,
  createKnowledgeBase,
  uploadDocument,
  deleteKnowledgeBase,
} from '@/services/knowledgeService';

const KnowledgePage: React.FC = () => {
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedKb, setSelectedKb] = useState<any>(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listKnowledgeBases();
      setKnowledgeBases(Array.isArray(data) ? data : []);
    } catch {
      message.error('获取知识库列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = async (values: { name: string; description?: string }) => {
    try {
      await createKnowledgeBase(values.name, values.description);
      message.success('创建成功');
      setCreateModalOpen(false);
      form.resetFields();
      fetchData();
    } catch {
      message.error('创建失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteKnowledgeBase(id);
      message.success('已删除');
      fetchData();
    } catch {
      message.error('删除失败');
    }
  };

  const handleUploadProps = (kbId: string): UploadProps => ({
    name: 'file',
    multiple: true,
    accept: '.pdf,.txt,.md,.docx',
    customRequest: async ({ file, onSuccess, onError }) => {
      try {
        await uploadDocument(kbId, file as File);
        onSuccess?.({});
        message.success(`${(file as File).name} 上传成功`);
        fetchData();
      } catch (e: any) {
        onError?.(e);
        message.error(`上传失败: ${e.message || '未知错误'}`);
      }
    },
  });

  const statusMap: Record<string, { color: string; text: string }> = {
    ACTIVE: { color: 'green', text: '正常' },
    BUILDING: { color: 'blue', text: '构建中' },
    ERROR: { color: 'red', text: '异常' },
  };

  const columns = [
    {
      title: '知识库名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <Space>
          <DatabaseOutlined style={{ color: '#1890ff' }} />
          <strong>{text}</strong>
        </Space>
      ),
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '文档数',
      dataIndex: 'documentCount',
      key: 'documentCount',
      width: 100,
      align: 'center' as const,
    },
    {
      title: '切片数',
      dataIndex: 'chunkCount',
      key: 'chunkCount',
      width: 100,
      align: 'center' as const,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const s = statusMap[status] || { color: 'default', text: status };
        return <Tag color={s.color}>{s.text}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<UploadOutlined />}
            onClick={() => {
              setSelectedKb(record);
              setUploadModalOpen(true);
            }}
          >
            上传文档
          </Button>
          <Popconfirm
            title="确定删除该知识库？所有文档和索引将被清除。"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const totalDocs = knowledgeBases.reduce((sum, kb) => sum + (kb.documentCount || 0), 0);
  const totalChunks = knowledgeBases.reduce((sum, kb) => sum + (kb.chunkCount || 0), 0);

  return (
    <PageContainer title="知识库管理" subTitle="上传文档，构建 RAG 知识库">
      {/* Stats */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic title="知识库数量" value={knowledgeBases.length} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="总文档数" value={totalDocs} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="总切片数" value={totalChunks} />
          </Card>
        </Col>
      </Row>

      {/* Table */}
      <Card
        title="知识库列表"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建知识库
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={knowledgeBases}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 个知识库` }}
        />
      </Card>

      {/* Create Modal */}
      <Modal
        title="新建知识库"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="例如：产品手册、技术文档" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="知识库用途说明（可选）" rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Upload Modal */}
      <Modal
        title={`上传文档到：${selectedKb?.name || ''}`}
        open={uploadModalOpen}
        onCancel={() => setUploadModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setUploadModalOpen(false)}>
            关闭
          </Button>,
        ]}
      >
        <Upload.Dragger {...handleUploadProps(selectedKb?.id || '')}>
          <p className="ant-upload-drag-icon">
            <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">支持 PDF、TXT、Markdown、DOCX 格式，单文件最大 50MB</p>
        </Upload.Dragger>
      </Modal>
    </PageContainer>
  );
};

export default KnowledgePage;
