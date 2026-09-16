const endpoints: Record<string, string> = {
  options: "/forecast/options",
  forecast: "/forecast",
};

async function proxy(
  request: Request,
  context: { params: Promise<{ resource: string }> },
) {
  const { resource } = await context.params;
  if (
    !endpoints[resource] ||
    (request.method === "POST") !== (resource === "forecast")
  ) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }
  try {
    const response = await fetch(
      `${(process.env.BACKEND_URL || "https://demandpulse-zgbx.onrender.com").replace(/\/$/, "")}${endpoints[resource]}`,
      {
        method: request.method,
        headers: { "Content-Type": "application/json" },
        ...(request.method === "POST" ? { body: await request.text() } : {}),
        cache: "no-store",
        signal: AbortSignal.timeout(30000),
      },
    );
    if (response.status >= 500)
      return Response.json(
        {
          detail:
            "The forecast service encountered an error. Please try again.",
        },
        { status: 502 },
      );
    return Response.json(await response.json(), { status: response.status });
  } catch {
    return Response.json(
      {
        detail:
          "Cannot reach the forecast service. Start the FastAPI server and try again.",
      },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
