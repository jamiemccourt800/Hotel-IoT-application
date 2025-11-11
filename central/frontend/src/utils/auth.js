export const login = async (username, password) => {
  await new Promise((resolve) => setTimeout(resolve, 500)); // simulate delay

  const users = [
    { username: "admin", password: "1Password", role: "admin", name: "Administrator" },
    { username: "user", password: "1Password", role: "user", name: "User1" },
  ];

  const user = users.find(
    (u) => u.username === username && u.password === password
  );

  if (!user) throw new Error("Invalid username or password");

  localStorage.setItem("user", JSON.stringify(user));
  return user;
};

export const logout = () => {
  localStorage.removeItem("user");
};
