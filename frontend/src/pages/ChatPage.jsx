import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import BackButton from "../components/BackButton";

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Welcome! Upload your notes, PDF, audio, or ask any educational question.",
    },
  ]);
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const activeSubject = useMemo(() => localStorage.getItem("subject") || "General", []);
  const activeTopic = useMemo(() => localStorage.getItem("topic") || "Current Topic", []);
  const messagesEndRef = useRef(null);
  const audioChunksRef = useRef([]);
  const mediaRecorderRef = useRef(null);
  const mountedRef = useRef(true);
  const streamRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const cleanupRecording = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;

      if (
        mediaRecorderRef.current &&
        mediaRecorderRef.current.state !== "inactive"
      ) {
        mediaRecorderRef.current.stop();
      }

      cleanupRecording();
    };
  }, [cleanupRecording]);

  const sendQuestion = async () => {
    if (!question.trim() || loading || recording) return;

    const userQuestion = question.trim();
    setLoading(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", text: userQuestion },
      { role: "assistant", text: "Thinking...", status: true },
    ]);

    setQuestion("");

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: userQuestion,
        }),
      });

      if (!response.ok) {
        throw new Error("Text request failed.");
      }

      const data = await response.json();

      if (!mountedRef.current) return;

      setMessages((prev) => [
        ...prev.filter((message) => !message.status),
        {
          role: "assistant",
          text: data.answer || "I could not generate an answer.",
        },
      ]);
    } catch (error) {
      if (!mountedRef.current) return;

      setMessages((prev) => [
        ...prev.filter((message) => !message.status),
        {
          role: "assistant",
          text: error.message || "Error connecting to backend.",
        },
      ]);
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }
  };

  const startRecording = async () => {
    if (loading || recording) return;

    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Voice recording is not supported in this browser.",
        },
      ]);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      if (!mountedRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      const recorder = new MediaRecorder(stream);

      streamRef.current = stream;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current = [...audioChunksRef.current, event.data];
        }
      };

      recorder.onstop = async () => {
        if (!mountedRef.current) {
          cleanupRecording();
          return;
        }
        const chunks = audioChunksRef.current;
        if (chunks.length === 0) {
          cleanupRecording();
          setRecording(false);
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              text: "No audio was recorded.",
            },
          ]);
          return;
        }
        const audioBlob = new Blob(chunks, {
          type: recorder.mimeType || "audio/webm",
        });
        const formData = new FormData();

        if (!mountedRef.current) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        formData.append("file", audioBlob, "recording.webm");
        setRecording(false);
        setLoading(true);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: "Transcribing...", status: true },
        ]);
        cleanupRecording();

        try {
          const response = await fetch("http://127.0.0.1:8000/ask-voice", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            throw new Error("Voice request failed.");
          }

          const data = await response.json();

          if (!mountedRef.current) return;

          setMessages((prev) => [
            ...prev.filter((message) => !message.status),
            {
              role: "user",
              text: data.transcript || "Voice message",
            },
            {
              role: "assistant",
              text: data.answer || "I could not generate an answer.",
            },
          ]);
          audioChunksRef.current = [];
        } catch (error) {
          if (!mountedRef.current) return;

          setMessages((prev) => [
            ...prev.filter((message) => !message.status),
            {
              role: "assistant",
              text: error.message || "Error transcribing audio. Please try again.",
            },
          ]);
        } finally {
          if (mountedRef.current) {
            setLoading(false);
          }
        }
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch (error) {
      cleanupRecording();
      setRecording(false);
      setLoading(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            error.name === "NotAllowedError"
              ? "Microphone permission was denied."
              : "Could not start microphone recording.",
        },
      ]);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-sky-950 via-cyan-950 to-blue-950 text-white">
      <div className="relative z-10 flex h-screen">
        <main className="flex-1 flex flex-col p-6">
          <BackButton />
          <div className="mb-5 backdrop-blur-xl bg-white/10 border border-cyan-400/20 rounded-3xl p-5">
            <h1 className="text-4xl font-bold text-cyan-300">Education AI</h1>
            <div className="mt-2 text-cyan-100 text-sm space-y-1">
              <div><span className="font-semibold">Subject:</span> {activeSubject}</div>
              <div><span className="font-semibold">Topic:</span> {activeTopic}</div>
            </div>
          </div>

          <div className="flex-1 backdrop-blur-xl bg-white/10 border border-cyan-400/20 rounded-3xl p-6 overflow-y-auto space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-2xl rounded-3xl p-5 ${message.role === "user"
                    ? "bg-cyan-500/20 border border-cyan-400/20"
                    : "bg-white/10"
                  } whitespace-pre-wrap`}
                >
                  {message.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="mt-5 backdrop-blur-xl bg-white/10 border border-cyan-400/20 rounded-3xl p-4 flex items-center gap-3">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendQuestion();
                }
              }}
              placeholder="Ask anything..."
              disabled={recording || loading}
              rows={1}
              aria-label="Question input"
              className="flex-1 bg-transparent outline-none placeholder-cyan-200 resize-none disabled:opacity-60"
            />

            <button
              type="button"
              onClick={sendQuestion}
              disabled={loading || recording || !question.trim()}
              className="px-8 py-3 rounded-2xl bg-cyan-500 hover:bg-cyan-400 font-semibold transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              Send
            </button>

            <button
              type="button"
              onClick={recording ? stopRecording : startRecording}
              disabled={loading}
              aria-label={recording ? "Stop recording" : "Start recording"}
              className="px-8 py-3 rounded-2xl bg-cyan-500 hover:bg-cyan-400 font-semibold transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {recording ? "Stop" : "Mic"}
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
