import type { Part, ToolStatus } from "../store/chat";

/** [while running, when finished] */
const TOOL_LABELS: Record<string, [string, string]> = {
  web_search: ["Searching the web", "Searched the web"],
  wikipedia: ["Reading Wikipedia", "Read Wikipedia"],
  fetch_url: ["Opening a page", "Opened a page"],
  get_weather: ["Checking the weather", "Checked the weather"],
  calculator: ["Calculating", "Calculated"],
  get_current_datetime: ["Checking the time", "Checked the time"],
  search_knowledge_base: ["Searching your documents", "Searched your documents"],
  save_memory: ["Saving to memory", "Saved to memory"],
  search_memory: ["Recalling memory", "Recalled memory"],
  list_files: ["Listing files", "Listed files"],
  read_file: ["Reading a file", "Read a file"],
  write_file: ["Writing a file", "Wrote a file"],
  python_repl: ["Running Python", "Ran Python"],
  send_email: ["Sending an email", "Sent an email"],
};

const STEP_LABELS: Record<string, string> = {
  retrieve: "Searched your documents",
  grade: "Checked the results are relevant",
  rewrite: "Rewrote the search query",
  planner: "Drafted a research plan",
  research_one: "Researched one step",
};

export const isTraceStep = (node: string) => node in STEP_LABELS;
export const stepLabel = (node: string) => STEP_LABELS[node] ?? node;

export function toolLabel(name: string, status: ToolStatus): string {
  const pair = TOOL_LABELS[name] ?? [`Running ${name}`, `Ran ${name}`];
  if (status === "held") return `Waiting to run: ${pair[0].toLowerCase()}`;
  if (status === "rejected") return `Skipped (rejected): ${pair[0].toLowerCase()}`;
  return status === "running" ? pair[0] : pair[1];
}

/** One-line summary of the most meaningful argument. */
export function argSummary(args: Record<string, unknown>): string {
  const first = ["query", "expression", "city", "to", "path", "url", "code", "content", "timezone"].find((k) => k in args);
  const value = first ? String(args[first]) : Object.values(args)[0];
  return value == null ? "" : String(value).split("\n")[0].slice(0, 90);
}

export const isTrace = (p: Part) => p.kind !== "text" && p.kind !== "reasoning";

export const TOOL_CATEGORY_LABELS: Record<string, string> = {
  web: "Web",
  utility: "Utilities",
  knowledge: "Documents",
  memory: "Memory",
  files: "Files",
  code: "Code",
  communication: "Communication",
};
