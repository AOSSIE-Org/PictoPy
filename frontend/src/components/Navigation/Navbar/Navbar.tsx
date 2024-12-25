export function Navbar(props: { title?: string }) {
  return (

    <div>
      <header className="flex w-full flex-row items-center justify-center align-middle">
        <div className="mt-3 flex h-16 w-[50%] items-center justify-between rounded-3xl bg-[#333333] px-16 mb-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <img src="/tauri.svg" height={'20px'} width={'20px'} alt="" />
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
        </div>
      </header>
    </div>
  
  );
}