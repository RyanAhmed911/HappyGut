/** Parse a `text/event-stream` body read from fetch (EventSource can't POST a photo). */
export interface SseEvent {
  event: string;
  data: unknown;
}

export function parseSseBlock(block: string): SseEvent | null {
  let event = "message";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
  }
  if (!data.length) return null;
  try {
    return { event, data: JSON.parse(data.join("\n")) };
  } catch {
    return null;
  }
}

export async function readSse(response: Response, onEvent: (e: SseEvent) => void): Promise<void> {
  if (!response.body) throw new Error("no_stream");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let cut = buffer.indexOf("\n\n");
    while (cut !== -1) {
      const parsed = parseSseBlock(buffer.slice(0, cut));
      if (parsed) onEvent(parsed);
      buffer = buffer.slice(cut + 2);
      cut = buffer.indexOf("\n\n");
    }
  }
  const last = parseSseBlock(buffer.trim());
  if (last) onEvent(last);
}
