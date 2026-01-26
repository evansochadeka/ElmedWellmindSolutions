import type { Express } from "express";
import { type Server } from "http";
import { createProxyMiddleware } from "http-proxy-middleware";
import { spawn } from "child_process";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // Start Python backend from root
  const pythonProcess = spawn("python3", ["app.py"], {
    stdio: "inherit",
    env: { ...process.env, PYTHONPATH: "." },
  });

  pythonProcess.on("error", (err) => {
    console.error("Failed to start Python backend:", err);
  });

  // Cleanup on exit
  process.on("exit", () => {
    pythonProcess.kill();
  });

  // Proxy API requests to Python backend
  app.use(
    "/api",
    createProxyMiddleware({
      target: "http://127.0.0.1:5001",
      changeOrigin: true,
      logLevel: "debug",
      onError: (err, req, res) => {
        console.error("Proxy error:", err);
        res.status(502).json({ message: "Backend unavailable" });
      },
    })
  );

  return httpServer;
}
