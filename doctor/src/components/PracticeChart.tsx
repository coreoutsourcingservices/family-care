import { useEffect, useRef } from "react";
import Chart from "chart.js/auto";
import type { ChartConfiguration, ChartType } from "chart.js";
type Props = {
  type: "line" | "doughnut" | "bar";
  labels: string[];
  values: number[];
  label: string;
  colors?: string[];
  showLegend?: boolean;
};
export default function PracticeChart({
  type,
  labels,
  values,
  label,
  showLegend = false,
  colors = ["#7560ff", "#198bff", "#13cbbb", "#f668b3"],
}: Props) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const key = JSON.stringify({ type, labels, values, label, colors });
  useEffect(() => {
    if (!canvas.current) return;
    const chart = new Chart(canvas.current, {
      type,
      data: {
        labels,
        datasets: [
          {
            label,
            data: values,
            backgroundColor: type === "line" ? "#8c6aff25" : colors,
            borderColor: type === "line" ? "#8060ff" : "#ffffff",
            borderWidth: type === "line" ? 2 : 3,
            ...(type === "line"
              ? {
                  fill: true,
                  tension: 0.35,
                  pointRadius: 3,
                  pointBackgroundColor: "#ffffff",
                  pointBorderColor: "#8060ff",
                }
              : {}),
            ...(type === "bar" ? { borderRadius: 6, maxBarThickness: 35 } : {}),
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: { legend: { display: false }, tooltip: { enabled: true } },
        ...(type === "doughnut"
          ? { cutout: "75%" }
          : {
              scales: {
                x: {
                  grid: { display: false },
                  ticks: {
                    color: "#7b87a3",
                    maxTicksLimit: 7,
                    font: { size: 10 },
                  },
                },
                y: {
                  beginAtZero: true,
                  ticks: { precision: 0, color: "#7b87a3", font: { size: 10 } },
                  grid: { color: "#e9edf8" },
                },
              },
            }),
      },
    } as ChartConfiguration<ChartType>);
    return () => chart.destroy();
  }, [key]);
  return (
    <>
      <div className={"dr-chartjs dr-chartjs-" + type}>
        <canvas
          ref={canvas}
          role="img"
          aria-label={
            label + ": " + labels.map((l, i) => l + " " + values[i]).join(", ")
          }
        />
        {showLegend && values.every((v) => !v) && (
          <span className="dr-chart-no-data">No records yet</span>
        )}
      </div>
      {showLegend && (
        <ul className="dr-chart-legend">
          {labels.map((name, i) => (
            <li key={name}>
              <i style={{ background: colors[i % colors.length] }} />
              <span>{name}</span>
              <strong>{values[i]}</strong>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
