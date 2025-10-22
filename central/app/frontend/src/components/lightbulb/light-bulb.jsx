import React from "react";
import bulbon from "../../assets/bulb-on.png";
import bulboff from "../../assets/bulb-off.png";

const LightBulb = ({ lighton }) => {
  return (
    <div className="text-center w-1/2 mx-auto">
      {!lighton ? (
        <img
          src={bulboff}
          alt="bulb off"
          width={250}
          style={{ objectFit: "contain" }}
        />
      ) : (
        <img
          src={bulbon}
          alt="bulb on"
          width={250}
          style={{ objectFit: "contain" }}
        />
      )}
    </div>
  );
};

export default LightBulb;
