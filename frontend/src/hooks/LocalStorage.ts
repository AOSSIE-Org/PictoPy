import { useState } from "react";

export function useLocalStorage(key: string, initialValue: string) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      if (item === null) return initialValue;
      return item ? item : initialValue;
    } catch (error) {
      console.log(error);
      return initialValue;
    }
  });

  const setValue = (value: string) => {
    try {
      setStoredValue(value);
      localStorage.setItem("folderPath", value);
    } catch (error) {
      console.log(error);
    }
  };

  return [storedValue, setValue];
}
