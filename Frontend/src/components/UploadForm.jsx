import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { useAuthContext } from "../context/AuthContext";

export default function UploadForm() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthContext();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    const validTypes = ["image/jpeg", "image/png", "application/pdf"];
    if (!validTypes.includes(selectedFile.type)) {
      setError("Please upload a JPEG, PNG, or PDF file");
      return;
    }

    // Validate file size (5MB max)
    if (selectedFile.size > 5 * 1024 * 1024) {
      setError("File size must be less than 5MB");
      return;
    }

    setError(null);
    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileChange({ target: { files: [droppedFile] } });
    }
  };

  const handleSubmit = async () => {
    if (!file) return;

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post("/api/auth/upload/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      navigate("/result", {
        state: {
          status: response.data.status.toLowerCase(),
          confidence: response.data.confidence,
          fileName: file.name,
        },
      });
    } catch (error) {
      console.error("Error detecting tampering:", error);
      setError(
        error.response?.data?.error ||
          "An error occurred while processing your file"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h5 className="card-title mb-0">Upload ID Document</h5>
        <p className="card-text text-muted">
          Upload an image of your government-issued ID to check for tampering
        </p>
      </div>
      <div className="card-body">
        {error && (
          <div className="alert alert-danger mb-3" role="alert">
            {error}
          </div>
        )}
        <div
          className="border border-dashed rounded p-5 text-center cursor-pointer bg-white"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => document.getElementById("file-upload")?.click()}
        >
          <input
            id="file-upload"
            type="file"
            className="d-none"
            accept="image/jpeg,image/png,application/pdf"
            onChange={handleFileChange}
          />
          {previewUrl ? (
            <div className="mt-3">
              <img
                src={previewUrl}
                alt="Preview"
                className="img-fluid rounded mx-auto d-block"
                style={{ maxHeight: "256px" }}
              />
              <p className="mt-2 text-muted small">{file?.name}</p>
            </div>
          ) : (
            <>
              <div className="mx-auto text-muted mb-3">
                <i className="bi bi-cloud-arrow-up fs-1"></i>
              </div>
              <p className="text-muted">
                <span className="text-primary fw-medium">Click to upload</span>{" "}
                or drag and drop
              </p>
              <p className="small text-muted">JPEG, PNG, or PDF (Max 5MB)</p>
            </>
          )}
        </div>
        <div className="mt-3 d-flex justify-content-end">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={!file || isLoading}
          >
            {isLoading ? (
              <>
                <span
                  className="spinner-border spinner-border-sm me-2"
                  role="status"
                  aria-hidden="true"
                ></span>
                Analyzing...
              </>
            ) : (
              "Check for Tampering"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
