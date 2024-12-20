export function Navbar(props: { title?: string }) {
  return (
    <header className="flex w-full flex-row items-center justify-center align-middle">
      <div className="mb-4 mt-3 flex h-16 w-[50%] items-center justify-between rounded-3xl border border-white/10 bg-white/5 px-16 shadow-lg backdrop-blur-md backdrop-saturate-150">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 transition-all duration-300 hover:scale-105">
            <img src="/public/PictoPy_Logo.png" className="h-7" alt="" />
            <span className="font-sans text-lg font-bold text-gray-50 drop-shadow-sm">
              PictoPy
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-sans text-lg font-medium text-gray-50/90 drop-shadow-sm">
            Welcome {props.title || 'User'}
          </span>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
