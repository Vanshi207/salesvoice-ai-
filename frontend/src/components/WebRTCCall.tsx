"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "./ui";

const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL ?? "http://localhost:7860";

type Status = "idle" | "connecting" | "connected" | "ended" | "error";

export function WebRTCCall({ leadId, leadName, userId, userRole }:
  { leadId: string; leadName: string; userId: string; userRole: string }) {
  const [status, setStatus] = useState<Status>("idle");
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState("");
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pcIdRef = useRef<string>("");

  const cleanup = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }
    pcIdRef.current = "";
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  async function startCall() {
    setError("");
    setStatus("connecting");
    setSeconds(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });
      pcRef.current = pc;

      stream.getTracks().forEach((t) => pc.addTrack(t, stream));

      pc.ontrack = (e) => {
        if (audioRef.current) {
          audioRef.current.srcObject = e.streams[0];
          audioRef.current.play().catch(() => {});
        }
      };

      pc.onconnectionstatechange = () => {
        if (pc.connectionState === "connected") {
          setStatus("connected");
          timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
        }
        if (["disconnected", "failed", "closed"].includes(pc.connectionState)) {
          setStatus("ended");
          stream.getTracks().forEach((t) => t.stop());
          cleanup();
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      await new Promise<void>((resolve) => {
        if (pc.iceGatheringState === "complete") { resolve(); return; }
        const timer = setTimeout(resolve, 2000);
        pc.onicegatheringstatechange = () => {
          if (pc.iceGatheringState === "complete") { clearTimeout(timer); resolve(); }
        };
      });

      const resp = await fetch(`${AGENT_URL}/api/offer`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          sdp: pc.localDescription!.sdp,
          type: pc.localDescription!.type,
          request_data: { lead_id: leadId, lead_name: leadName, user_id: userId, user_role: userRole },
        }),
      });
      if (!resp.ok) throw new Error(`Agent returned ${resp.status}`);
      const answer = await resp.json();
      pcIdRef.current = answer.pc_id;
      await pc.setRemoteDescription(new RTCSessionDescription({ sdp: answer.sdp, type: answer.type }));
    } catch (e) {
      setError((e as Error).message);
      setStatus("error");
      cleanup();
    }
  }

  function endCall() {
    if (pcRef.current) {
      pcRef.current.getSenders().forEach((s) => { if (s.track) s.track.stop(); });
      pcRef.current.close();
    }
    setStatus("ended");
    cleanup();
  }

  const fmt = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;

  return (
    <div className="space-y-3">
      <audio ref={audioRef} autoPlay playsInline />
      <div className="flex items-center gap-3">
        {status === "idle" || status === "ended" || status === "error" ? (
          <Button onClick={startCall}>
            {status === "ended" ? "Call again" : "Talk to AI agent"}
          </Button>
        ) : status === "connecting" ? (
          <Button disabled>Connecting...</Button>
        ) : (
          <>
            <Button variant="danger" onClick={endCall}>End call</Button>
            <span className="text-sm font-medium text-green-700">Connected · {fmt}</span>
          </>
        )}
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {status === "connected" && (
        <p className="text-xs text-slate-400">
          Speak naturally — the AI agent will search the knowledge base to answer product questions.
        </p>
      )}
    </div>
  );
}
