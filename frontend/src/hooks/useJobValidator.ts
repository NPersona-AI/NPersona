"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAppStore, useHasHydrated } from "@/stores/appStore";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api";

/**
 * On mount, validates the persisted jobId against the backend.
 * If the job doesn't exist (404) or is in an error state, resets the
 * store and redirects to /upload automatically — no manual localStorage
 * cleanup needed.
 *
 * Waits for Zustand hydration before checking so Fast Refresh / page
 * refreshes don't fire a premature redirect while jobId is still null.
 */
export function useJobValidator() {
  const hasHydrated = useHasHydrated();
  const { jobId, resetJob } = useAppStore();
  const router = useRouter();
  const checked = useRef(false);

  useEffect(() => {
    // Don't do anything until localStorage has been read into the store
    if (!hasHydrated) return;
    if (checked.current || !jobId) return;
    checked.current = true;

    (async () => {
      try {
        const res = await fetch(`${API_BASE}/job/${jobId}/status`);
        if (res.status === 404) {
          console.error("[useJobValidator] Job 404 → resetting and going to /upload", jobId);
          resetJob();
          router.replace("/upload");
          return;
        }
        if (!res.ok) return; // network hiccup — don't reset
        const data = await res.json();
        console.debug("[useJobValidator] status check:", data.status, "for job", jobId);
        if (data.status === "error") {
          console.error("[useJobValidator] Job errored → resetting and going to /upload", data);
          resetJob();
          router.replace("/upload");
        } else if (data.status === "graph_ready" || data.status === "done") {
          console.debug("[useJobValidator] graph ready → going to /graph-explorer");
          router.replace("/graph-explorer");
        }
      } catch {
        // Network error — don't reset, let the user retry
      }
    })();
  }, [hasHydrated, jobId, resetJob, router]);
}
