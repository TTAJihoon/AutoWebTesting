const workflow = [
  "프로젝트 생성",
  "LLM 모드 선택",
  "TC JSON 가져오기",
  "TC 검토",
  "DOM 요약",
  "실행계획 JSON 가져오기",
  "Playwright 실행",
  "보고서 생성"
];

const mvpCards = [
  {
    title: "GPT 웹 결과물 업로드",
    body: "프로그램은 LLM을 직접 호출하지 않고 JSON 결과물을 검증해 사람이 보기 좋은 TC 화면으로 변환합니다."
  },
  {
    title: "안전한 실행계획",
    body: "GPT는 코드를 만들지 않고 제한된 action과 elementId만 포함한 JSON 계획을 생성합니다."
  },
  {
    title: "로컬 증적 저장",
    body: "실행 결과, 스크린샷, DOM 요약, 콘솔/네트워크 로그를 프로젝트 폴더에 저장합니다."
  }
];

export function App(): JSX.Element {
  return (
    <main className="app-shell">
      <section className="intro">
        <div>
          <p className="eyebrow">Windows local runner</p>
          <h1>AutoWebTesting</h1>
          <p className="summary">
            제품 매뉴얼과 기능리스트에서 생성한 테스트케이스를 검토하고, Playwright로 웹 제품을 실행 검증하는 로컬 시험 도구입니다.
          </p>
        </div>
        <div className="mode-panel">
          <span>1차 MVP 모드</span>
          <strong>GPT 웹 결과물 업로드</strong>
        </div>
      </section>

      <section className="workflow" aria-label="MVP workflow">
        {workflow.map((item, index) => (
          <div className="workflow-step" key={item}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <p>{item}</p>
          </div>
        ))}
      </section>

      <section className="card-grid">
        {mvpCards.map((card) => (
          <article className="info-card" key={card.title}>
            <h2>{card.title}</h2>
            <p>{card.body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
