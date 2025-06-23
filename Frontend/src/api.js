import axios from "axios";
import { ACCESS_TOKEN } from "./constants";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // Include cookies in requests
  // headers: {
  //   "Content-Type": "application/json",
  //   Accept: "application/json",
  // },
});

// // Add token to every request
// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem(ACCESS_TOKEN);
//   if (token) {
//     config.headers["Authorization"] = `Bearer ${token}`;
//   }
//   return config;
// });

// // Automatically refresh token on 401
// api.interceptors.response.use(
//   (response) => response,
//   async (error) => {
//     const originalRequest = error.config;

//     if (error.response?.status === 401 && !originalRequest._retry) {
//       originalRequest._retry = true;
//       try {
//         const refreshToken = localStorage.getItem("refresh");
//         if (refreshToken) {
//           const res = await axios.post(`${BASE_URL}/api/auth/token/refresh/`, {
//             refresh: refreshToken,
//           });
//           const newAccess = res.data.access;
//           localStorage.setItem(ACCESS_TOKEN, newAccess);
//           originalRequest.headers["Authorization"] = `Bearer ${newAccess}`;
//           return api(originalRequest);
//         }
//       } catch (refreshError) {
//         console.error("Token refresh failed:", refreshError);
//         localStorage.removeItem(ACCESS_TOKEN);
//         localStorage.removeItem("refresh");
//         window.location.href = "/login";
//       }
//     }

//     return Promise.reject(error);
//   }
// );

export default api;
