import { useEffect } from 'react';
import Logo from './logo'
import { Link } from 'react-router-dom';

const Header = () => {
  return (
       <div className="header flex flex-row justify-between shadow-[0_0_25px_rgba(0,0,0,0.9)] mb-5">
        <Logo/>
        <div className="text-white w-20">
          <Link onClick={() => {
            localStorage.removeItem("user");
            window.location.href = "/login";
          }} className="text-center">
            Logout
          </Link>
        </div>
      </div>
  )
}

export default Header
