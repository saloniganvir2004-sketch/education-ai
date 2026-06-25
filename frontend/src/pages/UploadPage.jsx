import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import LoadingSpinner from "../components/LoadingSpinner";

export default function UploadPage() {
  const navigate = useNavigate();

  const [selectedSubject, setSelectedSubject] = useState("General");

  useEffect(() => {
    const subject = localStorage.getItem("subject");
    if (subject) {
      setSelectedSubject(subject);
    }
  }, []);

  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDuplicateDialog, setShowDuplicateDialog] = useState(false);
  const [pendingUpload, setPendingUpload] = useState(false);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const uploadingRef = useRef(false);

  const uploadFile = async () => {
    if (!file) {
      setStatus("Please select a file");
      return;
    }

    if (!pendingUpload) {
      const topic = file.name.replace(/\.[^.]+$/, "");
      try {
        const res = await fetch(`http://127.0.0.1:8000/topics/exists?subject=${encodeURIComponent(selectedSubject)}&topic=${encodeURIComponent(topic)}`);
        if (res.ok) {
          const exists = await res.json();
          if (exists.exists) {
            setShowDuplicateDialog(true);
            return;
          }
        }
      } catch (_) {}
    }

    if (uploadingRef.current) return;
    uploadingRef.current = true;
    setLoading(true);

    const formData = new FormData();
    formData.append("subject", selectedSubject);
    formData.append("topic", file.name.replace(/\.[^.]+$/, ""));
    formData.append("file", file);
    formData.append("keep_both", replaceExisting ? "false" : "true");

    setStatus("Uploading...");

    try {
      if (replaceExisting) {
        const topic = file.name.replace(/\.[^.]+$/, "");
        const lookup = await fetch(`http://127.0.0.1:8000/uploads`);
        if (lookup.ok) {
          const { uploads } = await lookup.json();
          const existing = uploads.find(
            (u) =>
              u.subject === selectedSubject &&
              u.topic === topic
          );
          if (existing?.document_id) {
            await fetch(`http://127.0.0.1:8000/document/${existing.document_id}/cascade`, {
              method: "DELETE",
            });
          }
        }
        setReplaceExisting(false);
      }

      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      const uploadedTopic = data.topic || file.name.replace(/\.[^.]+$/, "");
      localStorage.setItem("topic", uploadedTopic);

      setUploads((prev) => [
        {
          name: file.name,
          status: "Ready",
          chunks: data.chunks_created,
        },
        ...prev,
      ]);

      setStatus(`Success! ${data.chunks_created} chunks created`);
      setPendingUpload(false);
      setReplaceExisting(false);

      setTimeout(() => {
        navigate("/chat");
      }, 1500);
    } catch (error) {
      setStatus(error.message || "Upload failed");
      setPendingUpload(false);
      setReplaceExisting(false);
    }
    finally {
      setLoading(false);
      uploadingRef.current = false;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-950 via-cyan-950 to-blue-950 text-white relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-10 left-10 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-10 right-10 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
      </div>

      <div className="relative z-10 max-w-[1600px] mx-auto p-8 grid lg:grid-cols-12 gap-8">
        <div className="lg:col-span-12 mb-4">
          <BackButton />
        </div>
        <div className="lg:col-span-8">
          <div className="mb-8 rounded-3xl p-8 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/20">
            <h1 className="text-6xl font-black">UPLOAD HUB</h1>
            <p className="text-cyan-100 mt-3 text-xl">
              Upload PDFs and create AI searchable knowledge.
            </p>
            <div className="mb-6 text-cyan-300 font-semibold">
              Selected Subject: {selectedSubject}
            </div>
          </div>

          <div className="min-h-[420px] rounded-[40px] border-4 border-dashed border-cyan-400/40 bg-cyan-500/5 flex flex-col items-center justify-center text-center mb-8">
            <div className="w-40 h-40 rounded-full border-4 border-cyan-400/40 flex items-center justify-center text-8xl mb-8 animate-pulse">
              ↑
            </div>

            <h2 className="text-3xl font-bold mb-4">Upload PDF Files</h2>

            <p className="text-cyan-100 mb-6">
              Select a PDF and upload it to the AI knowledge base
            </p>

            {loading && (
              <LoadingSpinner text="Uploading and processing..." />
            )}

            <input
              type="file"
              accept=".pdf, .docx, .txt, .mp3, .wav,.m4a, .mp4, .mov, .avi"
              onChange={(e) => setFile(e.target.files[0])}
              className="mb-4"
            />

            <button
              type="button"
              disabled={loading}
              onClick={uploadFile}
              className="px-8 py-4 rounded-2xl bg-cyan-500 hover:bg-cyan-400 transition font-bold text-lg"
            >
              Upload File
            </button>

            <p className="mt-4 text-cyan-300">{status}</p>
          </div>
        </div>

        <div className="backdrop-blur-xl bg-black/30 border border-cyan-400/20 rounded-3xl p-6">
          <h2 className="text-2xl font-bold text-cyan-300 mb-4">
            Recent Uploads
          </h2>

          <div className="space-y-3">
            {uploads.length === 0 ? (
              <div className="p-4 rounded-2xl bg-white/5">
                No uploads yet
              </div>
            ) : (
              uploads.map((upload, index) => (
                <div
                  key={index}
                  className="p-4 rounded-2xl bg-white/5 flex justify-between"
                >
                  <span>{upload.name}</span>
                  <span className="text-cyan-300">Ready</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {showDuplicateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full text-center text-black">
            <h3 className="text-xl font-bold mb-4">Duplicate Topic Detected</h3>
            <p className="mb-6">A topic with this name already exists. What would you like to do?</p>
            <div className="flex flex-col space-y-4">
              <button
                className="px-6 py-3 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700"
                onClick={() => {
                  setReplaceExisting(true);
                  setPendingUpload(true);
                  setShowDuplicateDialog(false);
                  uploadFile();
                }}
              >
                Replace Existing Topic
              </button>
              <button
                className="px-6 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700"
                onClick={() => {
                  setPendingUpload(true);
                  setShowDuplicateDialog(false);
                  uploadFile();
                }}
              >
                Keep Both
              </button>
              <button
                className="px-6 py-3 bg-gray-400 text-black rounded-xl font-semibold hover:bg-gray-500"
                onClick={() => {
                  setShowDuplicateDialog(false);
                  setPendingUpload(false);
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}