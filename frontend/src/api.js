const API_BASE_URL = "http://localhost:8000";

export async function triggerDQRule(payload) {
  const response = await fetch(`${API_BASE_URL}/create-and-trigger-dq-rule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function reprocessLast(payload) {
  const response = await fetch(`${API_BASE_URL}/reprocess-last`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}
