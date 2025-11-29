const RoomTile = ({hotel, id, occupied = false, number, roomInfoHandler }) => {

  return (
    <button
     onClick={roomInfoHandler}
      key={id}
    //   disabled={occupied}
      className={`p-4 rounded-xl border text-lg font-medium transition
                  ${
                    occupied
                      ? "bg-blue-100 border-blue-300 text-blue-500"
                      : "bg-green-100 border-green-300 text-green-700 hover:bg-green-200 hover:border-green-400"
                  }`}
    >
      Room {number}
      <div className="text-sm italic">
        {occupied ? "occupied" : "available"}
      </div>
    </button>
  );
};

export default RoomTile;
