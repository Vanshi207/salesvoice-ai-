import { useEffect } from "react";

export function usePolling(fn: () => void, active: boolean, ms = 3000) {
  useEffect(() => {
    if (!active) return;
    const id = setInterval(fn, ms);
    return () => clearInterval(id);
  }, [fn, active, ms]);
}
