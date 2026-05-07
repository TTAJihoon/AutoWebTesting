import { useMemo, useState, type ChangeEvent } from "react";
import type { DomSummary, ExecutionPlanPayload, ReviewStatus, TestCase } from "../../shared/types";
import type { SaveRunArtifactsResponse } from "../../main/runArtifacts";
import type { ExecutePlansResponse } from "../../runner/executor";
import { parseDomSummaryJson, parseExecutionPlanJson } from "./domPlanImport";
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

const planStatusLabels = {
  READY: "실행 가능",
  NEEDS_MAPPING_REVIEW: "매핑 검토",
  NOT_AUTOMATABLE: "자동화 불가",
  SKIPPED_RISK: "위험 제외"
};

const executionStatusLabels = {
  NOT_RUN: "미실행",
  COMPLETED: "수행 완료",
  BLOCKED: "실행 차단",
  MAPPING_FAILED: "매핑 실패",
  SCRIPT_FAILED: "스크립트 실패",
  SKIPPED_RISK: "위험 제외",
  MANUAL_REQUIRED: "수동 필요",
  CANCELLED: "취소"
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

  const [domSummary, setDomSummary] = useState<DomSummary | undefined>();
  const [domFileName, setDomFileName] = useState<string>("");
  const [domErrors, setDomErrors] = useState<string[]>([]);
  const [domWarnings, setDomWarnings] = useState<string[]>([]);
  const [targetUrl, setTargetUrl] = useState<string>("");
  const [showBrowser, setShowBrowser] = useState<boolean>(false);
  const [isCapturingDom, setIsCapturingDom] = useState<boolean>(false);

  const [executionPlanPayload, setExecutionPlanPayload] = useState<ExecutionPlanPayload | undefined>();
  const [planFileName, setPlanFileName] = useState<string>("");
  const [planErrors, setPlanErrors] = useState<string[]>([]);
  const [planWarnings, setPlanWarnings] = useState<string[]>([]);
  const [accountUsername, setAccountUsername] = useState<string>("");
  const [accountPassword, setAccountPassword] = useState<string>("");
  const [invalidPassword, setInvalidPassword] = useState<string>("invalid-password");
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<ExecutePlansResponse | undefined>();
  const [runErrors, setRunErrors] = useState<string[]>([]);
  const [isSavingRun, setIsSavingRun] = useState<boolean>(false);
  const [saveResult, setSaveResult] = useState<SaveRunArtifactsResponse | undefined>();
  const [saveErrors, setSaveErrors] = useState<string[]>([]);

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

  const approvedAutomationCases = useMemo(
    () =>
      testCases.filter(
        (testCase) =>
          testCase.reviewStatus === "APPROVED" &&
          testCase.automationTarget &&
          testCase.riskLevel !== "PROHIBITED"
      ),
    [testCases]
  );

  const stats = useMemo(() => {
    const approved = testCases.filter((testCase) => testCase.reviewStatus === "APPROVED").length;
    const risky = testCases.filter((testCase) => testCase.riskLevel === "HIGH" || testCase.riskLevel === "PROHIBITED").length;
    const needsReview = testCases.filter(
      (testCase) => testCase.reviewStatus === "DRAFT" || testCase.reviewStatus === "NEEDS_REVISION"
    ).length;

    return {
      total: testCases.length,
      approved,
      automationCandidates: approvedAutomationCases.length,
      risky,
      needsReview
    };
  }, [approvedAutomationCases.length, testCases]);

  const domRoleStats = useMemo(() => {
    const counts = new Map<string, number>();
    domSummary?.elements.forEach((element) => {
      counts.set(element.role, (counts.get(element.role) ?? 0) + 1);
    });
    return Array.from(counts.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [domSummary]);

  const planStats = useMemo(() => {
    const plans = executionPlanPayload?.executionPlans ?? [];
    return {
      total: plans.length,
      ready: plans.filter((plan) => plan.status === "READY").length,
      needsMappingReview: plans.filter((plan) => plan.status === "NEEDS_MAPPING_REVIEW").length,
      notAutomatable: plans.filter((plan) => plan.status === "NOT_AUTOMATABLE").length,
      skippedRisk: plans.filter((plan) => plan.status === "SKIPPED_RISK").length
    };
  }, [executionPlanPayload]);

  const runStats = useMemo(() => {
    const results = runResult?.results ?? [];
    return {
      total: results.length,
      passed: results.filter((result) => result.testResult === "P").length,
      failed: results.filter((result) => result.testResult === "F").length,
      notExecutable: results.filter((result) => result.testResult === "N/A").length
    };
  }, [runResult]);

  async function handleTestcaseFileChange(event: ChangeEvent<HTMLInputElement>) {
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
      resetDomAndPlan();
    }
  }

  async function handleDomFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const result = parseDomSummaryJson(await file.text());
    setDomFileName(file.name);
    setDomErrors(result.errors);
    setDomWarnings(result.warnings);

    if (result.payload && result.errors.length === 0) {
      setDomSummary(result.payload);
      resetPlan();
    }
  }

  async function handleCaptureDomSummary() {
    if (!targetUrl.trim()) {
      setDomErrors(["DOM을 생성할 URL을 입력해야 합니다."]);
      setDomWarnings([]);
      return;
    }

    setIsCapturingDom(true);
    setDomErrors([]);
    setDomWarnings([]);

    try {
      const summary = await window.autoWebTesting.captureDomSummary({
        url: targetUrl.trim(),
        showBrowser
      });
      setDomSummary(summary);
      setDomFileName("Playwright 자동 생성");
      setDomWarnings(summary.elements.length === 0 ? ["수집된 DOM 요소가 없습니다."] : []);
      resetPlan();
    } catch (error) {
      setDomErrors([error instanceof Error ? error.message : "DOM 요약 생성 중 알 수 없는 오류가 발생했습니다."]);
    } finally {
      setIsCapturingDom(false);
    }
  }

  async function handlePlanFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const result = parseExecutionPlanJson(await file.text(), testCases, domSummary);
    setPlanFileName(file.name);
    setPlanErrors(result.errors);
    setPlanWarnings(result.warnings);

    if (result.payload && result.errors.length === 0) {
      setExecutionPlanPayload(result.payload);
      setRunResult(undefined);
      setRunErrors([]);
    }
  }

  async function handleExecutePlans() {
    if (!executionPlanPayload || !domSummary) {
      setRunErrors(["실행계획과 DOM 요약이 모두 필요합니다."]);
      return;
    }

    setIsExecuting(true);
    setRunErrors([]);
    setRunResult(undefined);

    try {
      const result = await window.autoWebTesting.executePlans({
        plans: executionPlanPayload.executionPlans,
        domSummary,
        showBrowser,
        values: {
          "account.username": accountUsername,
          "account.password": accountPassword,
          "testData.invalidPassword": invalidPassword
        }
      });
      setRunResult(result);
      setSaveResult(undefined);
      setSaveErrors([]);
    } catch (error) {
      setRunErrors([error instanceof Error ? error.message : "실행 중 알 수 없는 오류가 발생했습니다."]);
    } finally {
      setIsExecuting(false);
    }
  }

  async function handleSaveRunArtifacts() {
    if (!runResult) {
      setSaveErrors(["저장할 실행 결과가 없습니다."]);
      return;
    }

    setIsSavingRun(true);
    setSaveErrors([]);

    try {
      const result = await window.autoWebTesting.saveRunArtifacts({
        runResult,
        testCases,
        domSummary,
        executionPlans: executionPlanPayload?.executionPlans
      });
      setSaveResult(result);
    } catch (error) {
      setSaveErrors([error instanceof Error ? error.message : "산출물 저장 중 알 수 없는 오류가 발생했습니다."]);
    } finally {
      setIsSavingRun(false);
    }
  }

  function updateReviewStatus(tcId: string, reviewStatus: ReviewStatus) {
    setTestCases((current) =>
      current.map((testCase) => (testCase.tcId === tcId ? { ...testCase, reviewStatus } : testCase))
    );
    resetPlan();
  }

  function toggleAutomationTarget(tcId: string) {
    setTestCases((current) =>
      current.map((testCase) =>
        testCase.tcId === tcId ? { ...testCase, automationTarget: !testCase.automationTarget } : testCase
      )
    );
    resetPlan();
  }

  function resetImport() {
    setPayload(undefined);
    setTestCases([]);
    setSelectedId(undefined);
    setFilterStatus("ALL");
    setFileName("");
    setErrors([]);
    setWarnings([]);
    resetDomAndPlan();
  }

  function resetDomAndPlan() {
    setDomSummary(undefined);
    setDomFileName("");
    setDomErrors([]);
    setDomWarnings([]);
    resetPlan();
  }

  function resetPlan() {
    setExecutionPlanPayload(undefined);
    setPlanFileName("");
    setPlanErrors([]);
    setPlanWarnings([]);
    setRunResult(undefined);
    setRunErrors([]);
    setSaveResult(undefined);
    setSaveErrors([]);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AutoWebTesting</p>
          <h1>테스트 실행 준비</h1>
        </div>
        <div className="mode-badge">
          <span>현재 단계</span>
          <strong>TC 검토 + DOM 매핑</strong>
        </div>
      </header>

      <section className="workspace-grid">
        <aside className="side-panel">
          <section className="panel-section">
            <h2>TC 가져오기</h2>
            <label className="file-picker">
              <input accept="application/json,.json" type="file" onChange={handleTestcaseFileChange} />
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
            <h2>TC 요약</h2>
            <div className="metric-list">
              <Metric label="전체" value={stats.total} />
              <Metric label="승인" value={stats.approved} />
              <Metric label="자동화 후보" value={stats.automationCandidates} />
              <Metric label="검토 필요" value={stats.needsReview} />
              <Metric label="위험" value={stats.risky} />
            </div>
          </section>

          <section className="panel-section">
            <h2>TC 검증</h2>
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

      <section className="mapping-grid">
        <article className="mapping-panel">
          <div className="panel-header">
            <div>
              <h2>DOM 요약</h2>
              <p>URL에서 자동 생성하거나 JSON 파일을 가져옵니다.</p>
            </div>
            <label className="compact-picker">
              <input accept="application/json,.json" type="file" onChange={handleDomFileChange} disabled={testCases.length === 0} />
              <span>DOM JSON 선택</span>
            </label>
          </div>

          <div className="mapping-content">
            <div className="capture-form">
              <input
                aria-label="DOM 요약 생성 URL"
                placeholder="https://example.com/login"
                type="url"
                value={targetUrl}
                onChange={(event) => setTargetUrl(event.target.value)}
              />
              <label className="check-row">
                <input type="checkbox" checked={showBrowser} onChange={(event) => setShowBrowser(event.target.checked)} />
                <span>브라우저 표시</span>
              </label>
              <button className="primary-button" type="button" onClick={handleCaptureDomSummary} disabled={isCapturingDom}>
                {isCapturingDom ? "생성 중" : "DOM 생성"}
              </button>
            </div>
            {domFileName ? <p className="file-name">{domFileName}</p> : <p className="muted">TC 업로드 후 DOM 요약 JSON을 선택합니다.</p>}
            {domSummary ? (
              <>
                <dl className="meta-list wide">
                  <div>
                    <dt>URL</dt>
                    <dd>{domSummary.page.url}</dd>
                  </div>
                  <div>
                    <dt>페이지 제목</dt>
                    <dd>{domSummary.page.title}</dd>
                  </div>
                  <div>
                    <dt>요소 수</dt>
                    <dd>{domSummary.elements.length}</dd>
                  </div>
                </dl>
                <div className="role-grid">
                  {domRoleStats.map(([role, count]) => (
                    <Metric key={role} label={role} value={count} />
                  ))}
                </div>
              </>
            ) : null}
            <MessageList tone="error" messages={domErrors} emptyText="DOM 오류 없음" />
            <MessageList tone="warning" messages={domWarnings} emptyText="DOM 경고 없음" />
          </div>
        </article>

        <article className="mapping-panel">
          <div className="panel-header">
            <div>
              <h2>실행계획</h2>
              <p>승인 TC와 DOM 요소를 기준으로 실행계획을 검증합니다.</p>
            </div>
            <label className="compact-picker">
              <input
                accept="application/json,.json"
                type="file"
                onChange={handlePlanFileChange}
                disabled={approvedAutomationCases.length === 0 || !domSummary}
              />
              <span>계획 JSON 선택</span>
            </label>
          </div>

          <div className="mapping-content">
            {planFileName ? <p className="file-name">{planFileName}</p> : <p className="muted">DOM 요약 후 GPT 웹에서 생성한 실행계획 JSON을 선택합니다.</p>}
            <div className="metric-list plan-metrics">
              <Metric label="전체 계획" value={planStats.total} />
              <Metric label="실행 가능" value={planStats.ready} />
              <Metric label="매핑 검토" value={planStats.needsMappingReview} />
              <Metric label="자동화 불가" value={planStats.notAutomatable} />
              <Metric label="위험 제외" value={planStats.skippedRisk} />
            </div>

            {executionPlanPayload ? (
              <div className="plan-list">
                {executionPlanPayload.executionPlans.map((plan) => (
                  <div className="plan-row" key={plan.tcId}>
                    <span className="mono">{plan.tcId}</span>
                    <strong>{planStatusLabels[plan.status]}</strong>
                    <span>{Math.round(plan.confidence * 100)}%</span>
                    <span>{plan.steps.length} steps</span>
                  </div>
                ))}
              </div>
            ) : null}

            <MessageList tone="error" messages={planErrors} emptyText="실행계획 오류 없음" />
            <MessageList tone="warning" messages={planWarnings} emptyText="실행계획 경고 없음" />
          </div>
        </article>
      </section>

      <section className="run-panel">
        <div className="panel-header">
          <div>
            <h2>시험 실행</h2>
            <p>실행계획 JSON을 제한된 Playwright 액션으로 수행합니다.</p>
          </div>
          <div className="header-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={handleSaveRunArtifacts}
              disabled={!runResult || isSavingRun}
            >
              {isSavingRun ? "저장 중" : "산출물 저장"}
            </button>
            <button
              className="primary-button"
              type="button"
              onClick={handleExecutePlans}
              disabled={!executionPlanPayload || !domSummary || isExecuting}
            >
              {isExecuting ? "실행 중" : "승인 계획 실행"}
            </button>
          </div>
        </div>

        <div className="run-content">
          <div className="credential-grid">
            <label>
              <span>account.username</span>
              <input value={accountUsername} onChange={(event) => setAccountUsername(event.target.value)} />
            </label>
            <label>
              <span>account.password</span>
              <input type="password" value={accountPassword} onChange={(event) => setAccountPassword(event.target.value)} />
            </label>
            <label>
              <span>testData.invalidPassword</span>
              <input value={invalidPassword} onChange={(event) => setInvalidPassword(event.target.value)} />
            </label>
          </div>

          <div className="metric-list run-metrics">
            <Metric label="전체" value={runStats.total} />
            <Metric label="P" value={runStats.passed} />
            <Metric label="F" value={runStats.failed} />
            <Metric label="실행 불가" value={runStats.notExecutable} />
          </div>

          <MessageList tone="error" messages={runErrors} emptyText="실행 오류 없음" />
          <MessageList tone="error" messages={saveErrors} emptyText="저장 오류 없음" />

          {saveResult ? (
            <div className="save-result">
              <h3>저장 완료</h3>
              <p>{saveResult.runDir}</p>
              <dl>
                <div>
                  <dt>Run ID</dt>
                  <dd>{saveResult.runId}</dd>
                </div>
                <div>
                  <dt>실패 패키지 항목</dt>
                  <dd>{saveResult.failedCaseCount}</dd>
                </div>
                <div>
                  <dt>결과 JSON</dt>
                  <dd>{saveResult.files.runResult}</dd>
                </div>
                <div>
                  <dt>실패 패키지 JSON</dt>
                  <dd>{saveResult.files.failurePackage}</dd>
                </div>
                <div>
                  <dt>HTML 보고서</dt>
                  <dd>{saveResult.files.htmlReport}</dd>
                </div>
              </dl>
            </div>
          ) : null}

          {runResult ? (
            <div className="result-list">
              {runResult.results.map((result) => (
                <article className="result-row" key={result.tcId}>
                  <div>
                    <span className="mono">{result.tcId}</span>
                    <strong>{executionStatusLabels[result.executionStatus]}</strong>
                  </div>
                  <div>
                    <span className={`result-pill result-${result.testResult.toLowerCase().replace("/", "")}`}>
                      {result.testResult}
                    </span>
                    <span>{result.steps.length} steps</span>
                  </div>
                  {result.failureDetail ? <p>{result.failureDetail}</p> : null}
                  {result.evidence?.screenshotPath ? <p>스크린샷: {result.evidence.screenshotPath}</p> : null}
                </article>
              ))}
            </div>
          ) : null}
        </div>
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
