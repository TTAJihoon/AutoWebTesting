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
    };
  }
}
