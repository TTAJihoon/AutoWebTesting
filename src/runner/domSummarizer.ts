export type DomSummaryElement = {
  elementId: string;
  role: string;
  tag: string;
  type?: string;
  label?: string;
  text?: string;
  placeholder?: string;
  name?: string;
  required?: boolean;
  visible: boolean;
  enabled: boolean;
  nearbyText?: string[];
  formId?: string;
};

export type DomSummary = {
  schemaVersion: "1.0.0";
  page: {
    url: string;
    title: string;
    heading?: string;
    visibleTextSummary?: string[];
  };
  forms?: Array<{
    formId: string;
    title?: string;
    elementIds: string[];
  }>;
  elements: DomSummaryElement[];
};

export function createEmptyDomSummary(url: string, title: string): DomSummary {
  return {
    schemaVersion: "1.0.0",
    page: {
      url,
      title,
      visibleTextSummary: []
    },
    forms: [],
    elements: []
  };
}
