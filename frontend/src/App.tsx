import { useEffect, useState } from 'react';
import { Alert, Button, Card, Col, ConfigProvider, Empty, Form, InputNumber, Layout, Progress, Radio, Row, Select, Space, Statistic, Table, Tag, Typography } from 'antd';
import { BookOutlined, ClockCircleOutlined, CrownOutlined, ExperimentOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import { api } from '@/api/client';
import { AbilityRadar } from '@/components/AbilityRadar';
import { useBankStore } from '@/store/useBankStore';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

function App() {
  const { dashboard, loading, error, paper, paperLoading, paperError, loadDashboard, demoLogin, generatePaper, loadPaper } = useBankStore();
  const [difficulty, setDifficulty] = useState('中级');
  const [amount, setAmount] = useState(10);
  const [lookup, setLookup] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [report, setReport] = useState<string[]>([]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    setAnswers({});
    setReport([]);
  }, [paper?.number]);

  async function submitExam() {
    if (!paper) return;
    const result = await api.submitExam(paper.number, answers);
    setReport([`得分 ${result.score}（答对 ${result.correct}/${result.total}）`, result.rank_hint, ...result.analysis]);
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
                  <Card
                    title="智能组卷练习"
                    extra={paper
                      ? <Tag color="green">试卷编号 No.{String(paper.number).padStart(4, '0')}</Tag>
                      : <Tag>尚未生成试卷</Tag>}
                  >
                    <Form layout="inline" className="paper-form">
                      <Form.Item label="难度">
                        <Select value={difficulty} onChange={setDifficulty} options={['入门', '初级', '中级', '高级', '专家'].map((value) => ({ value, label: value }))} />
                      </Form.Item>
                      <Form.Item label="题量">
                        <Select value={amount} onChange={setAmount} options={[10, 20, 30, 50].map((value) => ({ value, label: `${value} 题` }))} />
                      </Form.Item>
                      <Button type="primary" icon={<ExperimentOutlined />} loading={paperLoading} onClick={() => generatePaper(difficulty, amount)}>生成试卷</Button>
                      <Form.Item label="按编号回查">
                        <InputNumber min={1} value={lookup} onChange={(value) => setLookup(value)} placeholder="试卷编号" />
                      </Form.Item>
                      <Button icon={<SearchOutlined />} loading={paperLoading} disabled={!lookup} onClick={() => lookup && loadPaper(lookup)}>查询</Button>
                    </Form>

                    {paperError && <Alert type="error" message={paperError} showIcon className="block" />}

                    {!paper && !paperError && (
                      <Empty description="请选择难度和题量生成试卷，或输入编号回查历史试卷" className="block" />
                    )}

                    {paper && (
                      <>
                        <Space wrap className="block">
                          <Tag color="green">编号 No.{String(paper.number).padStart(4, '0')}</Tag>
                          <Tag color="blue">难度 {paper.difficulty}</Tag>
                          <Tag color={paper.actualAmount < paper.requestedAmount ? 'orange' : 'default'}>
                            题量 {paper.actualAmount}/{paper.requestedAmount}
                          </Tag>
                          {Object.entries(paper.typeCounts).map(([name, count]) => (
                            <Tag key={name}>{name} {count} 题</Tag>
                          ))}
                        </Space>

                        {paper.replacements.length > 0 && (
                          <Alert
                            type="info"
                            showIcon
                            className="block"
                            message="相邻难度补入说明"
                            description={paper.replacements
                              .map((item) => `${item.type}：补入 ${item.count} 题（${Object.entries(item.from).map(([from, count]) => `${from} ${count} 题`).join('，')}）`)
                              .join('；')}
                          />
                        )}

                        {paper.gaps.length > 0 && (
                          <Alert
                            type="warning"
                            showIcon
                            className="block"
                            message={`题池不足，已按实际题量 ${paper.actualAmount} 题生成`}
                            description={`各类型缺口：${paper.gaps.map((item) => `${item.type} 缺 ${item.missing} 题`).join('；')}`}
                          />
                        )}

                        <Space direction="vertical" size={16} className="question-list">
                          {paper.questions.map((question, index) => (
                            <Card key={question.id} size="small" className="question-card">
                              <Space wrap className="question-meta">
                                <Tag>{question.type}</Tag>
                                <Tag color="blue">{question.difficulty}</Tag>
                                <Tag color="gold">{question.knowledge}</Tag>
                                {question.substituted && <Tag color="orange">相邻难度补入</Tag>}
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
                      </>
                    )}
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
