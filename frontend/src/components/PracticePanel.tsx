import { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Empty,
  Form,
  InputNumber,
  Radio,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from 'antd';
import { ExperimentOutlined, FileSearchOutlined, HistoryOutlined } from '@ant-design/icons';
import { api } from '@/api/client';
import type { Paper, PaperSummary, Question } from '@/types/bank';

const { Title, Paragraph, Text } = Typography;

const DIFFICULTY_COLOR: Record<string, string> = {
  入门: 'green',
  初级: 'cyan',
  中级: 'blue',
  高级: 'geekblue',
  专家: 'purple',
};

function QuestionCard({ question, index, value, onChange }: {
  question: Question;
  index: number;
  value: string | undefined;
  onChange: (option: string) => void;
}) {
  return (
    <Card size="small" className="question-card">
      <Space wrap className="question-meta">
        <Tag>{question.type}</Tag>
        <Tag color={DIFFICULTY_COLOR[question.difficulty] ?? 'default'}>
          {question.difficulty}
          {question.replaced && `（目标：${question.requested_difficulty}）`}
        </Tag>
        {question.replaced && <Tag color="orange">{question.replace_label}</Tag>}
        <Tag color="gold">{question.knowledge}</Tag>
      </Space>
      <Title level={5}>{index + 1}. {question.stem}</Title>
      <Radio.Group value={value} onChange={(event) => onChange(event.target.value)}>
        <Space direction="vertical">
          {question.options.map((option) => <Radio key={option} value={option}>{option}</Radio>)}
        </Space>
      </Radio.Group>
      <Paragraph className="explain">解析：{question.explanation}</Paragraph>
    </Card>
  );
}

export function PracticePanel() {
  const [difficulty, setDifficulty] = useState('中级');
  const [amount, setAmount] = useState(10);
  const [paper, setPaper] = useState<Paper | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [history, setHistory] = useState<PaperSummary[]>([]);
  const [lookupNo, setLookupNo] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<string>('');
  const [report, setReport] = useState<string[]>([]);

  async function refreshHistory() {
    try {
      const result = await api.paperHistory();
      setHistory(result.papers);
    } catch {
      // 历史加载失败不阻塞组卷主流程
    }
  }

  useEffect(() => {
    refreshHistory();
  }, []);

  function openPaper(next: Paper) {
    setPaper(next);
    setAnswers({});
    setReport([]);
  }

  async function handleGenerate() {
    setLoading(true);
    setNotice('');
    try {
      const result = await api.generatePaper(difficulty, amount);
      openPaper(result.paper);
      await refreshHistory();
      setLookupNo(result.paper.paperNo);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '生成试卷失败');
    } finally {
      setLoading(false);
    }
  }

  async function handleLookup(no?: number) {
    const target = no ?? lookupNo ?? undefined;
    if (!target) {
      setNotice('请输入要回查的试卷编号。');
      return;
    }
    setLoading(true);
    setNotice('');
    try {
      const result = await api.getPaper(target);
      openPaper(result.paper);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '回查试卷失败');
      setPaper(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (!paper) {
      return;
    }
    try {
      const result = await api.submitExam(answers, paper.paperNo);
      setReport([
        `试卷 ${result.paperCode} 得分 ${result.score}（答对 ${result.correctCount}/${result.totalCount} 题）`,
        result.rank_hint,
        ...result.analysis,
      ]);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '提交失败');
    }
  }

  const gapEntries = paper ? Object.entries(paper.typeGaps) : [];

  return (
    <Card
      title="智能组卷练习"
      extra={<Tag color="green">试卷快照可回查</Tag>}
    >
      <Form layout="inline" className="paper-form">
        <Form.Item label="难度">
          <Select
            value={difficulty}
            onChange={setDifficulty}
            options={['入门', '初级', '中级', '高级', '专家'].map((value) => ({ value, label: value }))}
          />
        </Form.Item>
        <Form.Item label="题量">
          <Select
            value={amount}
            onChange={setAmount}
            options={[10, 20, 30, 50].map((value) => ({ value, label: `${value} 题` }))}
          />
        </Form.Item>
        <Form.Item>
          <Button type="primary" icon={<ExperimentOutlined />} loading={loading} onClick={handleGenerate}>
            生成试卷
          </Button>
        </Form.Item>
      </Form>

      <Space wrap className="lookup-bar">
        <InputNumber
          min={1}
          placeholder="试卷编号"
          value={lookupNo}
          onChange={(value) => setLookupNo(value)}
          addonBefore="编号"
        />
        <Button icon={<FileSearchOutlined />} onClick={() => handleLookup()}>按编号回查</Button>
        <Select
          className="history-select"
          placeholder={<span><HistoryOutlined /> 历史试卷</span>}
          value={paper?.paperNo}
          onChange={(value) => handleLookup(value)}
          options={history.map((item) => ({
            value: item.paperNo,
            label: `${item.paperCode}｜${item.difficulty}｜${item.actualAmount}/${item.requestedAmount} 题${item.shortage ? '｜有缺口' : ''}`,
          }))}
        />
      </Space>

      {notice && <Alert type="warning" message={notice} showIcon className="block" closable onClose={() => setNotice('')} />}

      <Spin spinning={loading}>
        {!paper ? (
          <Empty description="选择难度与题量后生成试卷，或输入编号回查旧试卷" className="paper-empty" />
        ) : (
          <>
            <Descriptions
              size="small"
              column={{ xs: 1, sm: 2, lg: 3 }}
              bordered
              className="paper-meta"
              items={[
                { key: 'code', label: '试卷编号', children: <Text strong copyable>{paper.paperCode}</Text> },
                {
                  key: 'amount',
                  label: '实际/选定题量',
                  children: (
                    <Text type={paper.shortage ? 'danger' : undefined} strong>
                      {paper.actualAmount} / {paper.requestedAmount} 题
                    </Text>
                  ),
                },
                { key: 'difficulty', label: '选定难度', children: paper.difficulty },
                {
                  key: 'replaced',
                  label: '相邻难度补入',
                  children: paper.replacementCount > 0
                    ? <Tag color="orange">{paper.replacementCount} 题</Tag>
                    : <Tag>无</Tag>,
                },
                { key: 'created', label: '生成时间', children: paper.createdAt ? new Date(paper.createdAt).toLocaleString('zh-CN') : '-' },
              ]}
            />

            <Alert
              className="block"
              type={paper.replacementCount > 0 ? 'warning' : 'info'}
              showIcon
              message="替换说明"
              description={paper.replacementNote}
            />

            {paper.shortage && (
              <Alert
                className="block"
                type="error"
                showIcon
                message={`题池不足，缺少 ${paper.shortageCount} 题（未重复填充，当前为实际可出的最大题量）`}
                description={
                  <Space wrap>
                    {gapEntries.map(([type, gap]) => (
                      <Tag key={type} color="red">{type}缺 {gap} 题</Tag>
                    ))}
                  </Space>
                }
              />
            )}

            <Table
              className="block"
              size="small"
              pagination={false}
              rowKey="type"
              dataSource={Object.entries(paper.typeActual).map(([type, actual]) => ({
                type,
                quota: paper.typeQuota[type],
                actual,
                gap: paper.typeGaps[type] ?? 0,
              }))}
              columns={[
                { title: '题型', dataIndex: 'type' },
                { title: '目标题量', dataIndex: 'quota', width: 90 },
                { title: '实际题量', dataIndex: 'actual', width: 90 },
                {
                  title: '缺口',
                  dataIndex: 'gap',
                  width: 90,
                  render: (value: number) => (value > 0 ? <Tag color="red">{value}</Tag> : <Tag>0</Tag>),
                },
              ]}
            />

            <Space direction="vertical" size={16} className="question-list block">
              {paper.questions.map((question, index) => (
                <QuestionCard
                  key={`${paper.paperCode}-${question.id}`}
                  question={question}
                  index={index}
                  value={answers[question.id]}
                  onChange={(option) => setAnswers({ ...answers, [question.id]: option })}
                />
              ))}
            </Space>
            <Button type="primary" className="submit" onClick={handleSubmit}>提交并生成报告</Button>
            {report.length > 0 && (
              <Alert type="success" message="考试报告" description={report.join('；')} showIcon className="block" />
            )}
          </>
        )}
      </Spin>
    </Card>
  );
}
