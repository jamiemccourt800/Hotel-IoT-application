import { useEffect } from 'react'

const Logo = ({user = null}) => {
  useEffect(() => {
    if(user != null)
    {
      user += "'s"
    }
  })
  return (
            <div className="text-white momo-signature-regular text-lg p-3 py-3">
         {user}  IoT Dashboard
        </div>
  )
}

export default Logo
