import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import '@testing-library/jest-dom';
import VerticalLightSlider from "./components/brightness-slide/brightness-slider.jsx";

describe("VerticalLightSlider", () => {
  it("renders with initial value", () => {
    render(<VerticalLightSlider initialValue={42} />);
    expect(screen.getByText("42%")) .toBeInTheDocument();
  });

  it("calls onsliderChange when slider is committed", () => {
    const onsliderChange = jest.fn();
    render(<VerticalLightSlider initialValue={10} onsliderChange={onsliderChange} />);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: 55 } });
    fireEvent.mouseUp(slider);
    expect(onsliderChange).toHaveBeenCalled();
  });
});
