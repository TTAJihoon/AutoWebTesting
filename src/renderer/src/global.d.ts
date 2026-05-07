export {};

declare global {
  interface Window {
    autoWebTesting: {
      getAppInfo: () => Promise<{
        name: string;
        version: string;
        platform: string;
      }>;
    };
  }
}
