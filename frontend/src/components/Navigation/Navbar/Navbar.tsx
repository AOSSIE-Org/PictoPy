import { ThemeToggle } from "@/components/ThemeToggle";

export function Navbar(props: { title?: string }) {
  return (

    <>
      <header className="flex w-full flex-row items-center justify-center align-middle">
        <div className="mt-3 flex h-16 w-[50%] items-center justify-between rounded-3xl bg-theme-light dark:bg-theme-dark px-16 mb-4 border border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <img src="/tauri.svg" height={'20px'} width={'20px'} alt="" />
              <span className="font-sans text-lg font-bold text-theme-dark dark:text-theme-light">
                Pictopy
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="font-sans text-lg font-medium text-theme-dark dark:text-theme-light">
              Welcome {props.title || 'User'} 
            </span>
            <ThemeToggle/>
          </div>
        </div>
      </header>
    </>
  );
}

