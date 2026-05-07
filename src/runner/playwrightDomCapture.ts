import { chromium } from "playwright";
import type { DomElementRole, DomSummary, DomSummaryElement } from "../shared/types";

export type CaptureDomSummaryRequest = {
  url: string;
  showBrowser?: boolean;
};

type RawDomElement = Omit<DomSummaryElement, "role"> & {
  role: string;
};

type RawDomSummary = {
  page: DomSummary["page"];
  elements: RawDomElement[];
};

export async function captureDomSummary(request: CaptureDomSummaryRequest): Promise<DomSummary> {
  const url = normalizeHttpUrl(request.url);
  const browser = await chromium.launch({ headless: request.showBrowser !== true });

  try {
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => undefined);

    const rawSummary = await page.evaluate((): RawDomSummary => {
      const roleCandidates = [
        "input",
        "textarea",
        "button",
        "a",
        "select",
        "table",
        "h1",
        "h2",
        "h3",
        "[role]",
        "[contenteditable='true']"
      ].join(",");

      const normalizeText = (value: string | null | undefined): string | undefined => {
        const text = value?.replace(/\s+/g, " ").trim();
        return text && text.length > 0 ? text.slice(0, 160) : undefined;
      };

      const isVisible = (element: Element): boolean => {
        const htmlElement = element as HTMLElement;
        const style = window.getComputedStyle(htmlElement);
        const rect = htmlElement.getBoundingClientRect();
        return (
          style.display !== "none" &&
          style.visibility !== "hidden" &&
          Number(style.opacity) !== 0 &&
          rect.width > 0 &&
          rect.height > 0
        );
      };

      const findLabel = (element: Element): string | undefined => {
        const ariaLabel = normalizeText(element.getAttribute("aria-label"));
        if (ariaLabel) {
          return ariaLabel;
        }

        const ariaLabelledBy = element.getAttribute("aria-labelledby");
        if (ariaLabelledBy) {
          const labelText = ariaLabelledBy
            .split(/\s+/)
            .map((id) => normalizeText(document.getElementById(id)?.textContent))
            .filter(Boolean)
            .join(" ");
          if (labelText) {
            return labelText.slice(0, 160);
          }
        }

        if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement) {
          if (element.id) {
            const label = document.querySelector(`label[for="${CSS.escape(element.id)}"]`);
            const labelText = normalizeText(label?.textContent);
            if (labelText) {
              return labelText;
            }
          }

          const parentLabel = element.closest("label");
          const parentLabelText = normalizeText(parentLabel?.textContent);
          if (parentLabelText) {
            return parentLabelText;
          }
        }

        return undefined;
      };

      const roleOf = (element: Element): string => {
        const explicitRole = element.getAttribute("role");
        if (explicitRole) {
          return explicitRole;
        }

        const tagName = element.tagName.toLowerCase();
        if (tagName === "textarea") {
          return "textarea";
        }
        if (tagName === "button") {
          return "button";
        }
        if (tagName === "a") {
          return "link";
        }
        if (tagName === "select") {
          return "select";
        }
        if (tagName === "table") {
          return "table";
        }
        if (tagName === "h1" || tagName === "h2" || tagName === "h3") {
          return "heading";
        }
        if (element instanceof HTMLInputElement) {
          if (element.type === "checkbox") {
            return "checkbox";
          }
          if (element.type === "radio") {
            return "radio";
          }
          if (element.type === "file") {
            return "file";
          }
          return "textbox";
        }
        if ((element as HTMLElement).isContentEditable) {
          return "textbox";
        }
        return "unknown";
      };

      const visibleTexts = Array.from(document.body?.querySelectorAll("h1,h2,h3,label,button,a,p,span") ?? [])
        .filter(isVisible)
        .map((element) => normalizeText(element.textContent))
        .filter((text): text is string => Boolean(text))
        .slice(0, 80);

      const elements = Array.from(document.querySelectorAll(roleCandidates))
        .filter(isVisible)
        .slice(0, 250)
        .map((element, index) => {
          const htmlElement = element as HTMLElement;
          const input = element instanceof HTMLInputElement ? element : undefined;
          const textarea = element instanceof HTMLTextAreaElement ? element : undefined;
          const select = element instanceof HTMLSelectElement ? element : undefined;

          return {
            elementId: `el_${String(index + 1).padStart(4, "0")}`,
            role: roleOf(element),
            tag: element.tagName.toLowerCase(),
            type: input?.type,
            label: findLabel(element),
            text: normalizeText(element.textContent),
            placeholder: input?.placeholder || textarea?.placeholder || undefined,
            name: input?.name || textarea?.name || select?.name || undefined,
            required: input?.required ?? textarea?.required ?? select?.required ?? undefined,
            visible: true,
            enabled:
              !(input?.disabled ?? false) &&
              !(textarea?.disabled ?? false) &&
              !(select?.disabled ?? false) &&
              htmlElement.getAttribute("aria-disabled") !== "true",
            nearbyText: Array.from(htmlElement.parentElement?.querySelectorAll("label,span,p,button,a") ?? [])
              .map((nearby) => normalizeText(nearby.textContent))
              .filter((text): text is string => Boolean(text))
              .slice(0, 6)
          };
        });

      return {
        page: {
          url: window.location.href,
          title: document.title || "",
          heading: normalizeText(document.querySelector("h1,h2,h3")?.textContent),
          visibleTextSummary: Array.from(new Set(visibleTexts))
        },
        elements
      };
    });

    return {
      schemaVersion: "1.0.0",
      page: rawSummary.page,
      forms: [],
      elements: rawSummary.elements.map((element) => ({
        ...element,
        role: normalizeRole(element.role)
      }))
    };
  } finally {
    await browser.close();
  }
}

function normalizeHttpUrl(value: string): string {
  const url = new URL(value);

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("URL은 http 또는 https 주소여야 합니다.");
  }

  return url.href;
}

function normalizeRole(role: string): DomElementRole {
  const allowedRoles: DomElementRole[] = [
    "textbox",
    "textarea",
    "button",
    "link",
    "select",
    "checkbox",
    "radio",
    "file",
    "table",
    "menuitem",
    "heading",
    "text",
    "dialog",
    "unknown"
  ];

  return allowedRoles.includes(role as DomElementRole) ? (role as DomElementRole) : "unknown";
}
