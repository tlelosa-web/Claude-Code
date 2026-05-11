import { useEffect, useRef, useState } from "react";

function stableStringify(obj) {
  return JSON.stringify(obj, Object.keys(obj).sort());
}

export function useNameplatePreview(payload, opts) {
  const debounceMs = opts.debounceMs ?? 300;
  const endpoint = opts.endpoint;

  const [state, setState] = useState({
    url: null,
    status: "idle",
    error: null,
  });

  const debounceTimer = useRef(null);
  const abortRef = useRef(null);
  const lastUrlRef = useRef(null);
  const requestSeq = useRef(0);
  const lastPayloadKey = useRef("");

  useEffect(() => {
    const payloadKey = stableStringify(payload);
    if (payloadKey === lastPayloadKey.current) return;
    lastPayloadKey.current = payloadKey;

    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    debounceTimer.current = setTimeout(async () => {
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      const mySeq = ++requestSeq.current;

      setState((s) => ({ ...s, status: "updating", error: null }));

      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: payloadKey,
          signal: controller.signal,
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        if (mySeq !== requestSeq.current) return;

        const newUrl = URL.createObjectURL(blob);
        if (lastUrlRef.current) URL.revokeObjectURL(lastUrlRef.current);
        lastUrlRef.current = newUrl;

        setState({ url: newUrl, status: "ok", error: null });
      } catch (err) {
        if (err.name === "AbortError") return;
        setState((s) => ({ ...s, status: "error", error: err.message || "Preview failed" }));
      }
    }, debounceMs);

    return () => clearTimeout(debounceTimer.current);
  }, [payload, debounceMs, endpoint]);

  return state;
}