import { useLocation, useNavigate } from "react-router-dom";
import { useAuthContext } from "../context/AuthContext";
import api from "../api";

export default function ResultDisplay() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthContext();

  if (!state) {
    navigate("/");
    return null;
  }

  const { status, confidence, fileName, details } = state;

  return (
    <div className="card">
      <div className="card-header">
        <h5 className="card-title mb-0">Detection Results</h5>
        <p className="card-text text-muted">Results for: {fileName}</p>
      </div>
      <div className="card-body">
        <div
          className={`alert ${
            status === "original" ? "alert-success" : "alert-danger"
          }`}
        >
          <h5 className="alert-heading">
            {status === "original"
              ? "✅ Original Document"
              : "❌ Tampered Document"}
          </h5>
        </div>

        <div className="mb-4">
          <div className="d-flex justify-content-between mb-1">
            <span className="text-muted">Confidence Level:</span>
            <span className="fw-medium">{confidence}%</span>
          </div>
          <div className="progress">
            <div
              className={`progress-bar ${
                status === "original" ? "bg-success" : "bg-danger"
              }`}
              style={{ width: `${confidence}%` }}
            ></div>
          </div>
        </div>

        <div className="mb-4">
          <h6>
            {status === "original"
              ? "No signs of tampering detected"
              : "Potential tampering detected"}
          </h6>
          <p className="text-muted">
            {status === "original"
              ? "The document appears to be authentic with no signs of manipulation."
              : "The document shows signs of potential tampering. Please verify with additional checks."}
          </p>
        </div>
        {details && (
          <div className="mt-4">
            <h6>Detection Breakdown</h6>
            <pre className="bg-light p-3 rounded small">
              {JSON.stringify(details, null, 2)}
            </pre>
          </div>
        )}

        <div className="d-flex gap-2">
          <button className="btn btn-primary" onClick={() => navigate("/")}>
            Check Another Document
          </button>
          {!isAuthenticated && (
            <button
              className="btn btn-outline-primary"
              onClick={() => navigate("/register")}
            >
              Create Account to Save Results
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
