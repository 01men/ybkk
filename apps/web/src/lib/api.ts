import axios from 'axios';

// 客户端用相对路径（同源经 Next.js rewrite → 后端 8080）
export const api = axios.create({
  baseURL: '/api/backend',
  withCredentials: true,
  timeout: 30_000,
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);
