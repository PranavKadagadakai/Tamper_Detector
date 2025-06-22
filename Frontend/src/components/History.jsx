import { useState, useEffect } from "react";
import api from "../api";
import { useAuthContext } from "../context/AuthContext";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isAuthenticated } = useAuthContext();

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchHistory = async () => {
      try {
        const response = await api.get("/api/auth/history/");
        setHistory(response.data);
      } catch (error) {
        console.error("Error fetching history:", error);
        setError("Failed to load history. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="card">
        <div className="card-body text-center py-5">
          <h5>Please login to view your detection history</h5>
          <button
            className="btn btn-primary mt-3"
            onClick={() => navigate("/login")}
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h5 className="card-title mb-0">Detection History</h5>
        <p className="card-text text-muted">
          Your previous tamper detection results
        </p>
      </div>
      <div className="card-body">
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}
        {loading ? (
          <div className="text-center py-4">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-2 text-muted">Loading history...</p>
          </div>
        ) : history.length > 0 ? (
          <div className="list-group">
            {history.map((item) => (
              <div
                key={item.id}
                className={`list-group-item ${
                  item.result === "Original"
                    ? "list-group-item-success"
                    : "list-group-item-danger"
                }`}
              >
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <span className="fw-medium">
                      {item.result === "Original"
                        ? "✅ Original"
                        : "❌ Tampered"}
                    </span>
                    <span className="text-muted ms-2 small">
                      {item.confidence}% confidence
                    </span>
                  </div>
                  <span className="text-muted small">
                    {new Date(item.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="small mb-0 mt-1 text-muted">
                  {item.image.split("/").pop()}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4">
            <div className="text-muted mb-3">
              <i className="bi bi-file-earmark-text fs-1"></i>
            </div>
            <h6 className="text-muted">No history yet</h6>
            <p className="small text-muted">
              Perform some detections to see them appear here
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
