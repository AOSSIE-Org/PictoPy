import type React from "react"
import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLocalStorage } from "@/hooks/LocalStorage"
import { queryClient, usePictoMutation, usePictoQuery } from "@/hooks/useQueryExtensio"
import { addFolder, getProgress } from "../../../api/api-functions/images"
import { AlertCircle, CheckCircle, Loader2 } from "lucide-react"

interface ProgressiveFolderLoaderProps {
  additionalFolders?: string[]
}

const ProgressiveFolderLoader: React.FC<ProgressiveFolderLoaderProps> = ({ additionalFolders = [] }) => {
  const [storedFolderPaths] = useLocalStorage<string[]>("folderPaths", [])
  const [addedFolders, setAddedFolders] = useLocalStorage<string[]>("addedFolders", [])
  const [autoAdd] = useLocalStorage("auto-add-folder", "false")
  const [showError, setShowError] = useState(false)
  let isComplete = false;
  const combinedFolderPaths = Array.from(new Set([...storedFolderPaths, ...additionalFolders]))
  const { mutate: addFolderAPI, errorMessage } = usePictoMutation({
    mutationFn: addFolder,
    onSuccess: () => {
      setAddedFolders([...storedFolderPaths])
    },
    onError: () => {
      queryClient.invalidateQueries({ queryKey: ["all-images"] })
      queryClient.invalidateQueries({ queryKey: ["ai-tagging-images", "ai"] })
      setShowError(true)
      setTimeout(() => setShowError(false), 5000)
    },
    autoInvalidateTags: ["ai-tagging-images", "ai"],
  })

  const { successData: progress, isLoading } = usePictoQuery({
    queryFn: async () => await getProgress(),
    queryKey: ["ai-tagging-images", "ai", "progress"],
    refetchInterval: isComplete ? false : 1000,
    enabled: true,
  })

  const autoAddFolders = useCallback(() => {
    if (autoAdd === "true") {
      const foldersToAdd = combinedFolderPaths.filter((folder) => !addedFolders.includes(folder))
      if (foldersToAdd.length > 0) {
        addFolderAPI(foldersToAdd)
      }
    }
  }, [autoAdd])

  useEffect(() => {
    autoAddFolders()
  }, [autoAddFolders])

  useEffect(()=>{
    queryClient.invalidateQueries({ queryKey: ["all-images"] })
    queryClient.invalidateQueries({ queryKey: ["ai-tagging-images", "ai"] })
 }, [progress, addedFolders, autoAdd, addFolderAPI])

  const progressPercentage = typeof progress === "number" ? progress : 0
  isComplete = progressPercentage >= 100

  return (
    <>
      <div className="fixed top-0 left-0 right-0 z-[1000]">
        {/* Progress bar */}
        <AnimatePresence>
          {(isLoading || progressPercentage > 0) && progressPercentage < 100 && (
            <motion.div
              className="w-full h-1 bg-gray-200 overflow-hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, transition: { duration: 0.5, delay: 0.5 } }}
            >
              <motion.div
                className="h-full bg-gradient-to-r from-sky-400 to-blue-500"
                initial={{ width: 0 }}
                animate={{
                  width: `${progressPercentage}%`,
                  transition: { ease: "easeInOut" },
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Loading indicator */}
        <AnimatePresence>
          {(isLoading || progressPercentage > 0) && progressPercentage < 100 && (
            <motion.div
              className="fixed top-4 right-4 flex items-center gap-2 bg-white dark:bg-gray-800 shadow-md rounded-full px-3 py-1.5 text-sm"
              initial={{ y: -50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -50, opacity: 0 }}
            >
              <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
              <span>Processing folders... {progressPercentage.toFixed(0)}%</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Completion indicator */}
        <AnimatePresence>
          {isComplete && (
            <motion.div
              className="fixed top-4 right-4 flex items-center gap-2 bg-white dark:bg-gray-800 shadow-md rounded-full px-3 py-1.5 text-sm"
              initial={{ y: -50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -50, opacity: 0 }}
              onAnimationComplete={() => {
                if (isComplete) {
                    setTimeout(() => {
                        queryClient.invalidateQueries({ queryKey: ["all-images"] })
                        queryClient.invalidateQueries({ queryKey: ["ai-tagging-images", "ai"] })
                    }, 1000)
                }
              }}
            >
              <CheckCircle className="h-4 w-4 text-green-500" />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error message */}
        <AnimatePresence>
          {showError && errorMessage && (
            <motion.div
              className="fixed top-4 left-1/2 transform -translate-x-1/2 flex items-center gap-2 bg-white dark:bg-gray-800 shadow-md rounded-lg px-4 py-2 text-sm border-l-4 border-red-500 max-w-md"
              initial={{ y: -50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -50, opacity: 0 }}
            >
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
              <div>
                <p className="font-medium text-red-500">Error</p>
                <p className="text-gray-600 dark:text-gray-300">{errorMessage}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  )
}

export default ProgressiveFolderLoader