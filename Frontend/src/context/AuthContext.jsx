import { useState, useEffect, createContext, useContext } from "react";
import { jwtDecode } from "jwt-decode";
import api from "../api";
import { ACCESS_TOKEN } from "../constants";

const AuthContext = createContext();

export const useAuthContext = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem("refresh");
      if (!refresh) {
        setIsAuthenticated(false);
        return;
      }

      const res = await api.post("/api/auth/token/refresh/", {
        refresh: refresh,
      });
      if (res.status === 200) {
        localStorage.setItem(ACCESS_TOKEN, res.data.access);
        const decoded = jwtDecode(res.data.access);
        setUser({
          id: decoded.user_id,
          username: decoded.username,
        });
        setIsAuthenticated(true);
      } else {
        logout();
      }
    } catch {
      logout();
    }
  };

  const checkAuth = async () => {
    const accessToken = localStorage.getItem(ACCESS_TOKEN);
    if (!accessToken) {
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    try {
      const decoded = jwtDecode(accessToken);
      const currentTime = Date.now() / 1000;

      if (decoded.exp < currentTime) {
        await refreshToken();
      } else {
        setUser({
          id: decoded.user_id,
          username: decoded.username,
        });
        setIsAuthenticated(true);
      }
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(ACCESS_TOKEN);
    localStorage.removeItem("refresh");
    setIsAuthenticated(false);
    setUser(null);
  };

  useEffect(() => {
    checkAuth().catch((error) => {
      console.error("Error checking authentication:", error);
      logout();
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        loading,
        user,
        setIsAuthenticated,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
