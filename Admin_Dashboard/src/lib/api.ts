const API_BASE_URL = (import.meta.env as any).VITE_API_BASE_URL || "http://localhost:8000";

// Override locally by creating Admin_Dashboard/.env with:
// VITE_API_BASE_URL=https://api.yourdomain.com

export async function fetchSubmissions() {
  const res = await fetch(`${API_BASE_URL}/admin/submissions`);
  if (!res.ok) {
    throw new Error(`Failed to fetch submissions: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSubmission(id: string) {
  const res = await fetch(`${API_BASE_URL}/admin/submissions/${id}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch submission: ${res.statusText}`);
  }
  return res.json();
}

export async function generateCatalogImages(id: string, styles: string[]) {
  const res = await fetch(`${API_BASE_URL}/admin/submissions/${id}/generate-catalog`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ styles })
  });
  if (!res.ok) {
    throw new Error(`Failed to generate catalog images: ${res.statusText}`);
  }
  return res.json();
}
