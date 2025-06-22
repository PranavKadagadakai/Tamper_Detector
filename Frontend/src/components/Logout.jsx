import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthContext } from "../context/AuthContext.jsx";

function Logout() {
  const { setIsAuthenticated } = useAuthContext();
  const navigate = useNavigate();

  useEffect(() => {
    localStorage.clear();
    setIsAuthenticated(false); // ✅ update auth context
    navigate("/login");
  }, [setIsAuthenticated, navigate]);
  return null;
}

export default Logout;
