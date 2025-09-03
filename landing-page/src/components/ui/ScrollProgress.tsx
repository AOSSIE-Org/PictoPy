import { useEffect, useState } from "react"

export const ScrollProgress = () => {
  const [scrollPercentage, setScrollPercentage] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight
      const scrollPosition = window.scrollY
      const percentage = (scrollPosition / totalHeight) * 100
      setScrollPercentage(Math.round(percentage))
    }

    window.addEventListener("scroll", handleScroll)

    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <div className="fixed top-0 left-0 right-0 h-1 bg-gray-200 z-50">
      <div 
        className="h-full bg-green-500 transition-all duration-300 ease-out" 
        style={{ width: `${scrollPercentage}%` }}
      />
    </div>
  )
}
