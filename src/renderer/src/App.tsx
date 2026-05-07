import { useMemo, useState, type ChangeEvent } from "react";
import type { ReviewStatus, TestCase } from "../../shared/types";
import { parseTestcaseJson, type TestcaseImportPayload } from "./testcaseImport";

const reviewStatusLabels: Record<ReviewStatus, string> = {
  DRAFT: "초안",
  APPROVED: "승인",
  NEEDS_REVISION: "수정 필요",
  REJECTED: "반려",
  EXCLUDED: "제외",
  DEPRECATED: "폐기"
};

const reviewStatusOptions: ReviewStatus[] = ["APPROVED", "NEEDS_REVISION", "EXCLUDED", "REJECTED"];

const riskLevelLabels = {
  LOW: "낮음",
  MEDIUM: "주의",
  HIGH: "높음",
  PROHIBITED: "금지"
};

type FilterStatus = "ALL" | ReviewStatus;

export function App() {
  const [payload, setPayload] = useState<TestcaseImportPayload | undefined>();
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("ALL");
  const [fileName, setFileName] = useState<string>("");
  const [errors, setErrors] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);

  const selectedTestCase = useMemo(
    () => testCases.find((testCase) => testCase.tcId === selectedId) ?? testCases[0],
    [selectedId, testCases]
  );

  const filteredTestCases = useMemo(() => {
    if (filterStatus === "ALL") {
      return testCases;
    }
    return testCases.filter((testCase) => testCase.reviewStatus === filterStatus);
  }, [filterStatus, testCases]);

  const stats = useMemo(() => {
    const approved = testCases.filter((testCase) => testCase.reviewStatus === "APPROVED").length;
    const automationCandidates = testCases.filter(
      (testCase) =>
        testCase.reviewStatus === "APPROVED" &&
        testCase.automationTarget &&
        testCase.riskLevel !== "PROHIBITED"
    ).length;
    const risky = testCases.filter((testCase) => testCase.riskLevel === "HIGH" || testCase.riskLevel === "PROHIBITED").length;
    const needsReview = testCases.filter(
      (testCase) => testCase.reviewStatus === "DRAFT" || testCase.reviewStatus === "NEEDS_REVISION"
    ).length;

    return {
      total: testCases.length,
      approved,
      automationCandidates,
      risky,
      needsReview
    };
  }, [testCases]);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const result = parseTestcaseJson(await file.text());
    setFileName(file.name);
    setErrors(result.errors);
    setWarnings(result.warnings);

    if (result.payload && result.errors.length === 0) {
      setPayload(result.payload);
      setTestCases(result.payload.testCases);
      setSelectedId(result.payload.testCases[0]?.tcId);
      setFilterStatus("ALL");
    }
  }

  function updateReviewStatus(tcId: string, reviewStatus: ReviewStatus) {
    setTestCases((current) =>
      current.map((testCase) => (testCase.tcId === tcId ? { ...testCase, reviewStatus } : testCase))
    );
  }

  function toggleAutomationTarget(tcId: string) {
    setTestCases((current) =>
      current.map((testCase) =>
        testCase.tcId === tcId ? { ...testCase, automationTarget: !testCase.automationTarget } : testCase
      )
    );
  }

  function resetImport() {
    setPayload(undefined);
    setTestCases([]);
    setSelectedId(undefined);
    setFilterStatus("ALL");
    setFileName("");
    setErrors([]);
    setWarnings([]);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AutoWebTesting</p>
          <h1>테스트케이스 검토</h1>
        </div>
        <div className="mode-badge">
          <span>현재 단계</span>
          <strong>TC JSON 업로드</strong>
        </div>
      </header>

      <section className="workspace-grid">
        <aside className="side-panel">
          <section className="panel-section">
            <h2>가져오기</h2>
            <label className="file-picker">
              <input accept="application/json,.json" type="file" onChange={handleFileChange} />
              <span>TC JSON 선택</span>
            </label>
            {fileName ? <p className="file-name">{fileName}</p> : <p className="muted">업로드된 파일 없음</p>}
            {payload ? (
              <dl className="meta-list">
                <div>
                  <dt>생성 방식</dt>
                  <dd>{payload.sourceMode === "GPT_WEB_IMPORT" ? "GPT 웹 업로드" : "API"}</dd>
                </div>
                <div>
                  <dt>생성 강도</dt>
                  <dd>{payload.generationLevel === "STANDARD" ? "표준" : "상세"}</dd>
                </div>
              </dl>
            ) : null}
            <button className="secondary-button" type="button" onClick={resetImport} disabled={!fileName}>
              초기화
            </button>
          </section>

          <section className="panel-section">
            <h2>요약</h2>
            <div className="metric-list">
              <Metric label="전체" value={stats.total} />
              <Metric label="승인" value={stats.approved} />
              <Metric label="자동화 후보" value={stats.automationCandidates} />
              <Metric label="검토 필요" value={stats.needsReview} />
              <Metric label="위험" value={stats.risky} />
            </div>
          </section>

          <section className="panel-section">
            <h2>검증 메시지</h2>
            <MessageList tone="error" messages={errors} emptyText="오류 없음" />
            <MessageList tone="warning" messages={warnings} emptyText="경고 없음" />
          </section>
        </aside>

        <section className="review-panel">
          <div className="panel-header">
            <div>
              <h2>TC 목록</h2>
              <p>{filteredTestCases.length}개 표시</p>
            </div>
            <div className="filter-tabs" role="tablist" aria-label="검토 상태 필터">
              {(["ALL", "DRAFT", "APPROVED", "NEEDS_REVISION", "EXCLUDED"] as FilterStatus[]).map((status) => (
                <button
                  className={filterStatus === status ? "active" : ""}
                  key={status}
                  type="button"
                  onClick={() => setFilterStatus(status)}
                >
                  {status === "ALL" ? "전체" : reviewStatusLabels[status]}
                </button>
              ))}
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>TC_ID</th>
                  <th>분류</th>
                  <th>시나리오</th>
                  <th>상태</th>
                  <th>자동화</th>
                  <th>위험</th>
                </tr>
              </thead>
              <tbody>
                {filteredTestCases.length > 0 ? (
                  filteredTestCases.map((testCase) => (
                    <tr
                      className={selectedTestCase?.tcId === testCase.tcId ? "selected" : ""}
                      key={testCase.tcId}
                      onClick={() => setSelectedId(testCase.tcId)}
                    >
                      <td className="mono">{testCase.tcId}</td>
                      <td>
                        <span className="category-line">{testCase.majorCategory}</span>
                        <span className="subtle-line">
                          {testCase.middleCategory} / {testCase.minorCategory}
                        </span>
                      </td>
                      <td>{testCase.scenario}</td>
                      <td>
                        <span className={`status-pill status-${testCase.reviewStatus.toLowerCase()}`}>
                          {reviewStatusLabels[testCase.reviewStatus]}
                        </span>
                      </td>
                      <td>{testCase.automationTarget ? "대상" : "제외"}</td>
                      <td>
                        <span className={`risk-pill risk-${testCase.riskLevel.toLowerCase()}`}>
                          {riskLevelLabels[testCase.riskLevel]}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="empty-cell">
                      TC JSON을 업로드하면 목록이 표시됩니다.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="detail-panel">
          <div className="panel-header compact">
            <div>
              <h2>상세</h2>
              <p>{selectedTestCase?.tcId ?? "선택 없음"}</p>
            </div>
          </div>

          {selectedTestCase ? (
            <div className="detail-content">
              <Field label="테스트 시나리오" value={selectedTestCase.scenario} />
              <Field label="입력 / 사전조건" value={selectedTestCase.precondition} />
              <Field label="기대 출력 / 사후조건" value={selectedTestCase.expectedResult} />
              <Field label="자동화 사유" value={selectedTestCase.automationReason ?? "없음"} />
              <Field label="위험 사유" value={selectedTestCase.riskReason ?? "없음"} />

              <div className="button-group">
                {reviewStatusOptions.map((status) => (
                  <button
                    className={selectedTestCase.reviewStatus === status ? "primary-button" : "secondary-button"}
                    key={status}
                    type="button"
                    onClick={() => updateReviewStatus(selectedTestCase.tcId, status)}
                  >
                    {reviewStatusLabels[status]}
                  </button>
                ))}
              </div>

              <button className="wide-button" type="button" onClick={() => toggleAutomationTarget(selectedTestCase.tcId)}>
                자동화 {selectedTestCase.automationTarget ? "대상에서 제외" : "대상으로 지정"}
              </button>
            </div>
          ) : (
            <p className="empty-detail">선택된 테스트케이스가 없습니다.</p>
          )}
        </aside>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MessageList({
  messages,
  emptyText,
  tone
}: {
  messages: string[];
  emptyText: string;
  tone: "error" | "warning";
}) {
  if (messages.length === 0) {
    return <p className="message-empty">{emptyText}</p>;
  }

  return (
    <ul className={`message-list ${tone}`}>
      {messages.map((message) => (
        <li key={message}>{message}</li>
      ))}
    </ul>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="field-block">
      <span>{label}</span>
      <p>{value}</p>
    </div>
  );
}
