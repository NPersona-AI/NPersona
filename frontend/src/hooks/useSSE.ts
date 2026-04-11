"use client";

import { useEffect } from "react";
import { API } from "@/lib/api";

export type SSEHandler = (event: string, data: Record<string, unknown>) => void;

/**
 * Opens a persistent SSE connection to /job/:jobId/stream.
 * Calls onEvent for every named event received.
 * Automatically closes and cleans up on unmount or jobId change.
 */
export function useSSE(jobId: string, onEvent: SSEHandler) {
  useEffect(() => {
    const es = new EventSource(`${API}/job/${jobId}/stream`);

    const handle = (eventName: string) => (e: Event) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        onEvent(eventName, data);
      } catch {
        /* ignore malformed frames */
      }
    };

    const events = [
      "stage_changed",
      "log_message",
      "node_created",
      "edge_created",
      "persona_born",
      "personas_complete",
      "error",
    ];

    events.forEach((name) => es.addEventListener(name, handle(name)));
    es.onerror = () => es.close();

    return () => {
      events.forEach((name) => es.removeEventListener(name, handle(name)));
      es.close();
    };
  }, [jobId]); // onEvent intentionally omitted — callers must use useCallback or stable refs
}
