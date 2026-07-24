import type { Config } from '@jest/types';

const config: Config.InitialOptions = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
  },
  moduleNameMapper: {
    '^@/config/Backend$': '<rootDir>/__mocks__/Backend.ts',
    '^config/Backend$': '<rootDir>/__mocks__/Backend.ts',
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|sass|scss)$': 'identity-obj-proxy',
    'utils/isProd$': '<rootDir>/__mocks__/isProd.ts',
  },
  transformIgnorePatterns: ['/node_modules/(?!(ldrs)/)'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
};

export default config;
