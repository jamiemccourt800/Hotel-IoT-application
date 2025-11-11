import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import '@testing-library/jest-dom';
import TemperatureSlider from "./components/temperature-slider/temp-slider.jsx";

describe("TemperatureSlider", () => {
  it("renders with initial value", () => {
    render(<TemperatureSlider initialValue={25} />);
    expect(screen.getByText("25°C")).toBeInTheDocument();
  });

  it("calls onSliderChange when slider is committed", () => {
    const onSliderChange = jest.fn();
    render(<TemperatureSlider initialValue={20} onSliderChange={onSliderChange} />);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: 28 } });
    fireEvent.mouseUp(slider);
    expect(onSliderChange).toHaveBeenCalled();
  });
});
