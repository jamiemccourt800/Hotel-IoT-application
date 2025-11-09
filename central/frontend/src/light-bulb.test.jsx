import React from "react";
import { render, screen } from "@testing-library/react";
import '@testing-library/jest-dom';
import LightBulb from "./components/lightbulb/light-bulb.jsx";

describe("LightBulb", () => {
  it("shows bulb off image when lighton is false", () => {
    render(<LightBulb lighton={false} />);
    expect(screen.getByAltText("bulb off")).toBeInTheDocument();
  });

  it("shows bulb on image when lighton is true", () => {
    render(<LightBulb lighton={true} />);
    expect(screen.getByAltText("bulb on")).toBeInTheDocument();
  });
});
