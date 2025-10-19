import type { Config } from '@jest/types';

const config: Config.InitialOptions = {
  preset: 'ts-jest',z
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|sass|scss)$': 'identity-obj-proxy',
    'utils/isProd$': '<rootDir>/__mocks__/isProd.ts',
  },
  transformIgnorePatterns: ['/node_modules/(?!(ldrs)/)'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
};

export default config;
