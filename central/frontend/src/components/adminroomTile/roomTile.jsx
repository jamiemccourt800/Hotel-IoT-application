const RoomTile = ({hotel, id, occupied = false, number, roomInfoHandler }) => {

  return (
    <button
     onClick={roomInfoHandler}
      key={id}
    //   disabled={occupied}
      className={`p-4 rounded-xl border text-lg font-medium transition
                  ${
                    occupied
                      ? "bg-red-100 border-red-300 text-red-500 cursor-not-allowed"
                      : "bg-green-100 border-green-300 text-green-700 hover:bg-green-200 hover:border-green-400"
                  }`}
    >
      Room {number}
      <div className="text-sm italic">
        {occupied ? "Occupied" : "Available"}
      </div>
    </button>
  );
};

export default RoomTile;
