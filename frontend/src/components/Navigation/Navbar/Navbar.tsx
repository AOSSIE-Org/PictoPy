export function Navbar(props: { title?: string }) {
  return (
    <>
      <header className="flex h-16 w-full items-center justify-between bg-[#333333] px-6 ">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <img src="/Pictopy.svg" alt="" />
            <span className="text-lg font-bold font-sans text-gray-50">
              Pictopy
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-lg font-sans font-medium text-gray-50">
            Welcome {props.title || "User"}
          </span>
        </div>
      </header>
    </>
  );
}
