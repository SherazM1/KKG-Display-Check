import { getHealth } from "@/lib/api";

export async function ApiStatus() {
  const result = await getHealth();
  const connected = result.ok && result.data.status === "ok";
  if (process.env.NODE_ENV !== "development") return null;
  return <p className="api-status">Development API · {connected ? "Connected" : "Unavailable"}</p>;
}
