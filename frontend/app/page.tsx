"use client";

import { useEffect, useState, type FormEvent } from "react";

type Options = {
  stores: { store_nbr: number; city: string }[];
  families: string[];
  history_start: string;
  history_end: string;
};
type Forecast = {
  date: string;
  store_nbr: number;
  family: string;
  predicted_sales: number;
};
const shift = (date: string, days: number) => {
  const value = new Date(`${date}T00:00:00Z`);
  value.setUTCDate(value.getUTCDate() + days);
  return value.toISOString().slice(0, 10);
};
const displayDate = (date: string) =>
  new Date(`${date}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });

async function readResponse(response: Response) {
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Please check your forecast inputs and try again.",
    );
  return data;
}

export default function Home() {
  const [options, setOptions] = useState<Options | null>(null);
  const [date, setDate] = useState("");
  const [store, setStore] = useState("");
  const [family, setFamily] = useState("");
  const [promotion, setPromotion] = useState("0");
  const [result, setResult] = useState<Forecast | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    fetch("/api/options", { signal: controller.signal })
      .then(readResponse)
      .then((data: Options) => {
        setOptions(data);
        setDate(shift(data.history_end, 1));
        setStore(String(data.stores[0]?.store_nbr ?? ""));
        setFamily(
          data.families.includes("GROCERY I")
            ? "GROCERY I"
            : (data.families[0] ?? ""),
        );
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [retry]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const data = await fetch("/api/forecast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date,
          store_nbr: Number(store),
          family,
          onpromotion: Number(promotion),
        }),
      }).then(readResponse);
      if (!Number.isFinite(data.predicted_sales))
        throw new Error(
          "The service returned an invalid prediction. Please try again.",
        );
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to generate forecast.",
      );
    } finally {
      setBusy(false);
    }
  }

  const validDate =
    /^\d{4}-\d{2}-\d{2}$/.test(date) &&
    !Number.isNaN(Date.parse(`${date}T00:00:00Z`));
  const beyondHistory =
    options && validDate && date > shift(options.history_end, 1);

  return (
    <div className="shell">
      <header className="header">
        <a className="brand" href="/" aria-label="DemandPulse home">
          <span className="brand-icon">⌁</span>Demand<span>Pulse</span>
        </a>
        <span className="header-label">RETAIL INTELLIGENCE</span>
        <span className={`connection ${options ? "connected" : ""}`}>
          <i />
          {options
            ? "Service connected"
            : loading
              ? "Connecting…"
              : "Service unavailable"}
        </span>
      </header>
      <main>
        <div className="intro">
          <div>
            <span className="eyebrow">YOUR NEXT DAY, IN FOCUS</span>
            <h1>A clearer picture of demand.</h1>
            <p>Turn yesterday’s patterns into tomorrow’s plan.</p>
          </div>
          <span className="model-tag">
            DAILY FORECAST <span>↗</span>
          </span>
        </div>
        {error && (
          <div className="error" role="alert">
            {error}
            {!options && (
              <button type="button" onClick={() => setRetry(retry + 1)}>
                Retry connection
              </button>
            )}
          </div>
        )}
        <div className="workspace">
          <section
            className="card form-card"
            aria-labelledby="configure-heading"
          >
            <div className="section-heading">
              <span className="step">01</span>
              <div>
                <h2 id="configure-heading">Set up your forecast</h2>
                <p>Choose a store, a category, and a day.</p>
              </div>
            </div>
            <form onSubmit={submit} onChange={() => setResult(null)}>
              <fieldset disabled={!options || busy}>
                <label htmlFor="store">Store location</label>
                <select
                  id="store"
                  value={store}
                  onChange={(e) => setStore(e.target.value)}
                  required
                >
                  {!options && <option>Loading stores…</option>}
                  {options?.stores.map((s) => (
                    <option key={s.store_nbr} value={s.store_nbr}>
                      Store {String(s.store_nbr).padStart(2, "0")} · {s.city}
                    </option>
                  ))}
                </select>
                <label htmlFor="family">Product family</label>
                <select
                  id="family"
                  value={family}
                  onChange={(e) => setFamily(e.target.value)}
                  required
                >
                  {!options && <option>Loading categories…</option>}
                  {options?.families.map((f) => (
                    <option key={f}>{f}</option>
                  ))}
                </select>
                <div className="field-row">
                  <div>
                    <label htmlFor="date">Forecast date</label>
                    <input
                      id="date"
                      type="date"
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="promotion">Items on promotion</label>
                    <input
                      id="promotion"
                      type="number"
                      min="0"
                      max="2147483647"
                      step="1"
                      value={promotion}
                      onChange={(e) => setPromotion(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <p className="field-note">
                  Promotion count is the number of items on offer that day.
                </p>
                <button className="primary" type="submit" disabled={!validDate}>
                  {busy ? "Calculating forecast…" : "Generate forecast"}
                  <span aria-hidden="true">↗</span>
                </button>
              </fieldset>
            </form>
            <p className="form-footer">
              One store. One product family. One day ahead.
            </p>
          </section>
          <section
            className={`result-card ${result ? "has-result" : ""}`}
            aria-labelledby="result-heading"
            aria-live="polite"
            aria-busy={busy}
          >
            <div className="result-top">
              <span className="eyebrow">THE DEMAND OUTLOOK</span>
              <span className="outline-tag">XGBoost</span>
            </div>
            {result ? (
              <div className="result-content">
                <p id="result-heading">Predicted daily sales</p>
                <div className="prediction">
                  {result.predicted_sales.toLocaleString("en-US", {
                    maximumFractionDigits: 2,
                  })}
                  <span>sales units</span>
                </div>
                <p className="result-description">
                  {result.family} · Store {result.store_nbr}
                  <br />
                  {displayDate(result.date)}
                </p>
              </div>
            ) : (
              <div className="result-content">
                <div
                  className={`signal ${busy ? "pulsing" : ""}`}
                  aria-hidden="true"
                >
                  ▂ ▅ ▃ ▇ ▄ ▆
                </div>
                <h2 id="result-heading">
                  {busy
                    ? "Finding the pattern…"
                    : "Your next forecast starts here."}
                </h2>
                <p className="result-description">
                  {busy
                    ? "Looking at historical patterns for your selection."
                    : "Set your inputs and generate a forecast to see the expected daily demand."}
                </p>
              </div>
            )}
            <div className="result-bottom">
              <span className="spark">✧</span>
              <p>
                Informed by sales history, promotions,
                <br />
                store context, holidays, and oil prices.
              </p>
            </div>
          </section>
        </div>
        <section
          className="card history-card"
          aria-labelledby="history-heading"
        >
          <div className="history-header">
            <div className="section-heading">
              <span className="step">02</span>
              <div>
                <h2 id="history-heading">Every forecast has a history</h2>
                <p>
                  Only the days before your selected date inform its history
                  features.
                </p>
              </div>
            </div>
            <span className="subtle-tag">CALENDAR-AWARE</span>
          </div>
          <div className="timeline">
            <div>
              <span className="timeline-label">HISTORY WINDOW OPENS</span>
              <strong>
                {validDate ? displayDate(shift(date, -28)) : "Choose a date"}
              </strong>
              <small>28 calendar days before</small>
            </div>
            <div className="timeline-track" aria-hidden="true">
              <i />
              <span />
              <i />
            </div>
            <div>
              <span className="timeline-label">LAST INCLUDED DAY</span>
              <strong>{validDate ? displayDate(shift(date, -1)) : "—"}</strong>
              <small>Yesterday’s observations</small>
            </div>
            <div className="forecast-day">
              <span className="timeline-label">FORECAST DAY</span>
              <strong>{validDate ? displayDate(date) : "—"}</strong>
              <small>Excluded from history</small>
            </div>
          </div>
          <div className="history-notes">
            <p>
              <strong>Exact dates, always.</strong> Lags look back 1, 7, 14, and
              28 calendar days. Missing days stay missing; rolling averages
              require a complete window.
            </p>
            <p>
              <strong>Know your data.</strong>{" "}
              {options
                ? `Sales data spans ${displayDate(options.history_start)} to ${displayDate(options.history_end)}. Individual stores and families may have gaps.`
                : "Connect to the service to see the available data range."}
            </p>
          </div>
          {beyondHistory && (
            <p className="notice">
              This date extends beyond the next day of available sales history.
              Recent observations will be missing; this model does not generate
              them recursively.
            </p>
          )}
          {options && validDate && date <= options.history_end && (
            <p className="notice">
              This is a historical forecast and may overlap model training. It
              is not an independent accuracy estimate.
            </p>
          )}
        </section>
        <footer>
          <span>
            DemandPulse <span className="footer-dot">/</span> Small signals.
            Smarter planning.
          </span>
          <span>Daily estimates · Actual demand may vary</span>
        </footer>
      </main>
    </div>
  );
}
