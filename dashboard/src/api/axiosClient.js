import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

// --- JWT handling -----------------------------------------------------
// The dashboard is treated as its own client: it requests a token once per
// browser session (stored in-memory here, not localStorage — see the
// artifact storage rules) and attaches it to every request. On a 401 it
// clears and re-issues a token, then retries once.

let cachedToken = null;

async function getToken() {
  if (cachedToken) return cachedToken;
  const { data } = await axios.post("/api/auth/token", { client_id: "dashboard" });
  cachedToken = data.token;
  return cachedToken;
}

apiClient.interceptors.request.use(async (config) => {
  const token = await getToken();
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retried) {
      cachedToken = null;
      error.config._retried = true;
      error.config.headers.Authorization = `Bearer ${await getToken()}`;
      return apiClient.request(error.config);
    }
    return Promise.reject(error);
  }
);

// --- API surface --------------------------------------------------------

export const fetchThreats = (limit = 50, verdict) =>
  apiClient.get("/threats", { params: { limit, verdict } }).then((r) => r.data);

export const deleteThreat = (id) => apiClient.delete(`/threats/${id}`).then((r) => r.data);

export const fetchStats = () => apiClient.get("/stats").then((r) => r.data);

export const scanUrl = (url) => apiClient.post("/scan/url", { url }).then((r) => r.data);

export default apiClient;
