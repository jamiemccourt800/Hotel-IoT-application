import React from 'react'
import Logo from './logo'
import { Link } from 'react-router-dom'

const AdminHeader = () => {
  return (
       <div className="header flex flex-row justify-between shadow-[0_0_25px_rgba(0,0,0,0.9)]">
        <Logo user={"Admin"}/>
        <div className="text-white w-52 mx-10">
          <Link
            to="/admin/grafana"
            className="text-center"
           >
            Metrics Dashboard
          </Link>
          <Link onClick={() => {
            localStorage.removeItem("user");
            window.location.href = "/";
          }} className="text-center ml-6">
            Logout
          </Link>
        </div>
      </div>
  )
}

export default AdminHeader
