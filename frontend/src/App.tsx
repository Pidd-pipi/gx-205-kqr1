import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Col, ConfigProvider, Form, Layout, Progress, Radio, Row, Select, Space, Statistic, Table, Tag, Typography } from 'antd';
import { BookOutlined, ClockCircleOutlined, CrownOutlined, ExperimentOutlined, ReloadOutlined } from '@ant-design/icons';
import { api } from '@/api/client';
import { AbilityRadar } from '@/components/AbilityRadar';
import { useBankStore } from '@/store/useBankStore';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

function App() {
  const { dashboard, loading, error, loadDashboard, demoLogin } = useBankStore();
  const [difficulty, setDifficulty] = useState('中级');
  const [amount, setAmount] = useState(10);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [report, setReport] = useState<string[]>([]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const paper = useMemo(() => dashboard?.paper ?? [], [dashboard]);

  async function submitExam() {
    const result = await api.submitExam(answers);
    setReport([`得分 ${result.score}`, result.rank_hint, ...result.analysis]);
  }

  return (
    <ConfigProvider theme={{ token: { borderRadius: 8, colorPrimary: '#2f6b57' } }}>
      <Layout className="page">
        <Content className="shell">
          <section className="hero">
            <div>
              <Text className="eyebrow">GXLogic Bank</Text>
              <Title>逻辑推理题库系统</Title>
              <Paragraph>题型分类、智能组卷、答题解析、错题追踪、模拟考试和段位排名整合在同一个练习台。</Paragraph>
            </div>
            <Space wrap>
              <Button icon={<ReloadOutlined />} loading={loading} onClick={loadDashboard}>刷新</Button>
              <Button type="primary" icon={<CrownOutlined />} onClick={demoLogin}>演示登录</Button>
            </Space>
          </section>

          {error && <Alert type="error" message={error} showIcon className="block" />}

          {dashboard && (
            <>
              <Row gutter={[16, 16]} className="block">
                <Col xs={24} sm={12} lg={6}><Card><Statistic title="累计答题" value={dashboard.profile.totalAnswered} prefix={<BookOutlined />} /></Card></Col>
                <Col xs={24} sm={12} lg={6}><Card><Statistic title="正确率" value={dashboard.profile.correctRate} suffix="%" /></Card></Col>
                <Col xs={24} sm={12} lg={6}><Card><Statistic title="连续正确天数" value={dashboard.profile.streakDays} prefix={<ClockCircleOutlined />} /></Card></Col>
                <Col xs={24} sm={12} lg={6}><Card><Statistic title="当前段位" value={dashboard.profile.tier} prefix={<CrownOutlined />} /></Card></Col>
              </Row>

              <Row gutter={[16, 16]} className="block">
                <Col xs={24} lg={15}>
                  <Card title="智能组卷练习" extra={<Tag color="green">限时考试可扩展</Tag>}>
                    <Form layout="inline" className="paper-form">
                      <Form.Item label="难度">
                        <Select value={difficulty} onChange={setDifficulty} options={['入门', '初级', '中级', '高级', '专家'].map((value) => ({ value, label: value }))} />
                      </Form.Item>
                      <Form.Item label="题量">
                        <Select value={amount} onChange={setAmount} options={[10, 20, 30, 50].map((value) => ({ value, label: `${value} 题` }))} />
                      </Form.Item>
                      <Button icon={<ExperimentOutlined />} onClick={() => api.generatePaper(difficulty, amount)}>生成试卷</Button>
                    </Form>

                    <Space direction="vertical" size={16} className="question-list">
                      {paper.map((question, index) => (
                        <Card key={question.id} size="small" className="question-card">
                          <Space wrap className="question-meta">
                            <Tag>{question.type}</Tag>
                            <Tag color="blue">{question.difficulty}</Tag>
                            <Tag color="gold">{question.knowledge}</Tag>
                          </Space>
                          <Title level={5}>{index + 1}. {question.stem}</Title>
                          <Radio.Group value={answers[question.id]} onChange={(event) => setAnswers({ ...answers, [question.id]: event.target.value })}>
                            <Space direction="vertical">
                              {question.options.map((option) => <Radio key={option} value={option}>{option}</Radio>)}
                            </Space>
                          </Radio.Group>
                          <Paragraph className="explain">解析：{question.explanation}</Paragraph>
                        </Card>
                      ))}
                    </Space>
                    <Button type="primary" className="submit" onClick={submitExam}>提交并生成报告</Button>
                    {report.length > 0 && <Alert type="success" message="考试报告" description={report.join('；')} showIcon className="block" />}
                  </Card>
                </Col>

                <Col xs={24} lg={9}>
                  <Card title="学习进度雷达">
                    <AbilityRadar data={dashboard.radar} />
                  </Card>
                  <Card title="题型分类题库" className="stacked">
                    {dashboard.categories.map((category) => (
                      <div className="category-row" key={category.id}>
                        <Text>{category.name}</Text>
                        <Progress percent={category.accuracy} size="small" />
                      </div>
                    ))}
                  </Card>
                </Col>
              </Row>

              <Row gutter={[16, 16]} className="block">
                <Col xs={24} lg={12}>
                  <Card title="错题本与收藏">
                    <Table
                      size="small"
                      rowKey="id"
                      dataSource={dashboard.wrongBook}
                      pagination={false}
                      columns={[
                        { title: '题目', dataIndex: 'title' },
                        { title: '类型', dataIndex: 'type', width: 110 },
                        { title: '错误次数', dataIndex: 'mistakes', width: 90 },
                        { title: '最后练习', dataIndex: 'lastPracticed', width: 110 }
                      ]}
                    />
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="排行榜与段位">
                    <Table
                      size="small"
                      rowKey="rank"
                      dataSource={dashboard.rankings}
                      pagination={false}
                      columns={[
                        { title: '#', dataIndex: 'rank', width: 54 },
                        { title: '用户', dataIndex: 'name' },
                        { title: '段位', dataIndex: 'tier', width: 90 },
                        { title: '得分', dataIndex: 'score', width: 90 },
                        { title: '正确率', dataIndex: 'accuracy', width: 90, render: (value) => `${value}%` }
                      ]}
                    />
                  </Card>
                </Col>
              </Row>
            </>
          )}
        </Content>
      </Layout>
    </ConfigProvider>
  );
}

export default App;
