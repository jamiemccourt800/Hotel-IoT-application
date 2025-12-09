import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer
} from "recharts";
import { axiosInstance } from "../../utils/axiosInstance";

export default function MetricChart({
  hotelId,
  room,
  metric,
  hours = 6,
  metric_title
}) {
  const [data, setData] = useState([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await axiosInstance.get(
          `/api/metrics/timeseries?hotel_id=${hotelId}&room=${room}&metric=${metric}&hours=${hours}`
        );
        setData(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error("Error fetching metric data:", err);
        setData([]);
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [hotelId, room, metric, hours]);

  return (
    <div
      className="p-4 bg-white rounded-lg shadow my-10 mx-auto"
      style={{ width: "100%", maxWidth: 800, minWidth: 300, minHeight: 300 }}
    >
      <h2 className="text-lg font-semibold mb-2">{metric_title} Over Time</h2>

      {data.length === 0 ? (
        <p className="text-gray-500 text-sm">No data available</p>
      ) : (
        <ResponsiveContainer width="100%" aspect={2}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              type="number"
              domain={["auto", "auto"]}
              tickFormatter={(t) => new Date(t).toLocaleTimeString()}
            />
            <YAxis />
            <Tooltip labelFormatter={(t) => new Date(t).toLocaleString()} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#1f77b4"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
