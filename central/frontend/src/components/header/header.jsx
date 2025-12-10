import Logo from './logo'
import { useNavigate } from 'react-router-dom';

const Header = () => {
    const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/");
  };
  return (
       <div className="header flex flex-row justify-between shadow-[0_0_25px_rgba(0,0,0,0.9)] mb-5">
        <Logo/>
          <button onClick={handleLogout} className="hover:underline text-white font-semibold mr-6">
          Logout
        </button>
      </div>
  )
}

export default Header
