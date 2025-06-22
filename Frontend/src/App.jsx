import { Routes, Route } from "react-router-dom";
import UploadForm from "./components/UploadForm";
import ResultDisplay from "./components/ResultDisplay";
import Login from "./components/Login";
import Register from "./components/Register";
import History from "./components/History";
import ProtectedRoute from "./routes/ProtectedRoute";
import Logout from "./components/Logout";
import Navbar from "./components/Navbar";
import { AuthProvider } from "./context/AuthContext";
import "bootstrap/dist/css/bootstrap.min.css";

export default function App() {
  return (
    <AuthProvider>
      <div className="min-vh-100 bg-light">
        <Navbar />
        <main className="container py-4">
          <Routes>
            <Route path="/" element={<UploadForm />} />
            <Route path="/result" element={<ResultDisplay />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <History />
                </ProtectedRoute>
              }
            />
            <Route
              path="/logout"
              element={
                <ProtectedRoute>
                  <Logout />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  );
}
