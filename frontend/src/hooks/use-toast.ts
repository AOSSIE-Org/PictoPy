export const useToast = () => {
  const toast = ({
    title,
    description,
    variant = 'default',
  }: {
    title: string;
    description: string;
    variant?: 'default' | 'destructive';
  }) => {
    if (variant === 'destructive') {
      alert(`❌ ${title}\n${description}`);
    } else {
      alert(`✅ ${title}\n${description}`);
    }
  };

  return { toast };
};
