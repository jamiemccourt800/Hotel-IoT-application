import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Home component with Light and Temperature tabs', () => {
  render(<App />);
  const lightButton = screen.getByText(/Light/i);
  const tempButton = screen.getByText(/Temperature/i);
  expect(lightButton).toBeInTheDocument();
  expect(tempButton).toBeInTheDocument();
});
