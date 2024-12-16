export function Navbar(props: { title?: string }) {
  return (
    <div className="flex justify-center mt-4">
      <header className="flex h-16 w-1/2 rounded-full items-center justify-between bg-[#333333] px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <img src="/tauri.svg" height="20px" width="20px" alt="" />
            <span className="font-sans text-lg font-bold text-gray-50">
              Pictopy
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-sans text-lg font-medium text-gray-50">
            Welcome {props.title || 'User'}
          </span>
        </div>
      </header>
    </div>
  );
}