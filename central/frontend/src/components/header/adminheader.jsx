import React from 'react'
import Logo from './logo'
import { Link } from 'react-router-dom'

const AdminHeader = () => {
  return (
       <div className="header flex flex-row justify-between shadow-[0_0_25px_rgba(0,0,0,0.9)]">
        <Logo user={"Admin"}/>
        <div className='menu flex flex-row py-3 align-middle'>
        <div className="text-white rounded-md w-44">
          <Link
            to="/admin/grafana"
            className="text-center"
           >
            Metrics Dashboard
          </Link>
        </div>
        </div>
      </div>
  )
}

export default AdminHeader
