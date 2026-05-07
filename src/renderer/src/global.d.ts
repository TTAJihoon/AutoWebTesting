export {};

declare global {
  interface Window {
    autoWebTesting: {
      getAppInfo: () => Promise<{
        name: string;
        version: string;
        platform: string;
      }>;
      captureDomSummary: (request: { url: string; showBrowser?: boolean }) => Promise<import("../../shared/types").DomSummary>;
      executePlans: (request: {
        plans: import("../../shared/types").ExecutionPlan[];
        domSummary: import("../../shared/types").DomSummary;
        values: Record<string, string>;
        showBrowser?: boolean;
      }) => Promise<import("../../runner/executor").ExecutePlansResponse>;
      saveRunArtifacts: (request: {
        runResult: import("../../runner/executor").ExecutePlansResponse;
        testCases: import("../../shared/types").TestCase[];
        domSummary?: import("../../shared/types").DomSummary;
        executionPlans?: import("../../shared/types").ExecutionPlan[];
      }) => Promise<import("../../main/runArtifacts").SaveRunArtifactsResponse>;
    };
  }
}
