import type { ModelBody } from "../api/client";
import { useSettings } from "../store/settings";

export function currentModel(): ModelBody {
  const s = useSettings.getState();
  return { provider: s.provider, model: s.model, temperature: s.temperature, api_key: s.apiKeys[s.provider] || null };
}
