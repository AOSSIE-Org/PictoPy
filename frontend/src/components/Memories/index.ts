/**
 * Memories Component Exports
 *
 * Barrel file for clean imports across the application.
 * Import components like: import { MemoriesPage, MemoryCard } from '@/components/Memories'
 */

export { default as MemoriesPage } from './MemoriesPage';
export { default as MemoryCard } from './MemoryCard';
export { default as FeaturedMemoryCard } from './FeaturedMemoryCard';

// Export types if needed
export type { Memory, MemoryImage } from '@/services/memoriesApi';
