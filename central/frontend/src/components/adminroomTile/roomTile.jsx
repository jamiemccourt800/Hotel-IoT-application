const RoomTile = ({ id, status = "available", number, roomInfoHandler }) => {
  // Map status to colors
  const statusStyles = {
    available: {
      bg: "bg-purple-500",
      border: "border-purple-400",
      text: "text-purple-100",
      hoverBg: "hover:bg-purple-400",
      hoverBorder: "hover:border-purple-300",
      gradient: "bg-gradient-to-br from-purple-400/40 to-purple-500/20",
    },
    occupied: {
      bg: "bg-red-600",
      border: "border-red-500",
      text: "text-red-100",
      hoverBg: "hover:bg-red-500",
      hoverBorder: "hover:border-red-400",
      gradient: "bg-gradient-to-br from-red-500/40 to-red-600/20",
    },
    booked: {
      bg: "bg-yellow-600",
      border: "border-yellow-500",
      text: "text-yellow-100",
      hoverBg: "hover:bg-yellow-500",
      hoverBorder: "hover:border-yellow-400",
      gradient: "bg-gradient-to-br from-yellow-500/40 to-yellow-600/20",
    },
  };

  const styles = statusStyles[status] || statusStyles.available;

  return (
    <button
      onClick={roomInfoHandler}
      key={id}
      className={`group relative p-6 rounded-2xl border-2 transition-all duration-300 overflow-hidden
        ${styles.bg} ${styles.border} ${styles.hoverBg} ${styles.hoverBorder} hover:scale-105`}
    >
      <div className="relative z-10">
        <div className={`text-xl font-bold mb-2 transition-colors ${styles.text}`}>
          Room {number}
        </div>
        <div className={`text-sm font-medium uppercase tracking-wider transition-colors ${styles.text}`}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </div>
      </div>

      <div
        className={`absolute inset-0 opacity-0 group-hover:opacity-80 transition-opacity duration-300 ${styles.gradient}`}
      />
    </button>
  );
};

export default RoomTile;
