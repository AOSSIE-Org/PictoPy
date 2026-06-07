import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

// Target files relative to repo root
const rootPackageJsonPath = path.join(repoRoot, "package.json");
const frontendPackageJsonPath = path.join(repoRoot, "frontend", "package.json");
const cargoTomlPath = path.join(
  repoRoot,
  "frontend",
  "src-tauri",
  "Cargo.toml",
);

// Parse and validate CLI arguments
const newVersion = process.argv[2];
if (!newVersion) {
  console.error("Error: Please provide a version number (e.g., X.Y.Z).");
  process.exit(1);
}

const semverRegex = /^\d+\.\d+\.\d+$/;
if (!semverRegex.test(newVersion)) {
  console.error(
    "Error: Version must be in X.Y.Z format (digits only, no v prefix).",
  );
  process.exit(1);
}

// 1. Read files
let rootPackageJsonContent, frontendPackageJsonContent, cargoTomlContent;

try {
  rootPackageJsonContent = fs.readFileSync(rootPackageJsonPath, "utf8");
} catch (err) {
  console.error(
    `Error: Could not read root package.json at ${rootPackageJsonPath}`,
  );
  process.exit(1);
}

try {
  frontendPackageJsonContent = fs.readFileSync(frontendPackageJsonPath, "utf8");
} catch (err) {
  console.error(
    `Error: Could not read frontend package.json at ${frontendPackageJsonPath}`,
  );
  process.exit(1);
}

try {
  cargoTomlContent = fs.readFileSync(cargoTomlPath, "utf8");
} catch (err) {
  console.error(`Error: Could not read Cargo.toml at ${cargoTomlPath}`);
  process.exit(1);
}

// 2. Validate current versions and format
let oldRootVersion;
const rootVersionMatch = rootPackageJsonContent.match(
  /"version"\s*:\s*"([^"]+)"/,
);
if (!rootVersionMatch) {
  console.error('Error: Could not find "version" field in root package.json.');
  process.exit(1);
}
oldRootVersion = rootVersionMatch[1];

let oldFrontendVersion;
const frontendVersionMatch = frontendPackageJsonContent.match(
  /"version"\s*:\s*"([^"]+)"/,
);
if (!frontendVersionMatch) {
  console.error(
    'Error: Could not find "version" field in frontend package.json.',
  );
  process.exit(1);
}
oldFrontendVersion = frontendVersionMatch[1];

let oldCargoVersion;
const cargoVersionMatch = cargoTomlContent.match(/^version\s*=\s*"([^"]+)"/m);
if (!cargoVersionMatch) {
  console.error(
    "Error: Could not find standalone package version field in Cargo.toml.",
  );
  process.exit(1);
}
oldCargoVersion = cargoVersionMatch[1];

// 3. Perform replacements
const updatedRootJsonContent = rootPackageJsonContent.replace(
  /("version"\s*:\s*")([^"]+)(")/,
  `$1${newVersion}$3`,
);

const updatedFrontendJsonContent = frontendPackageJsonContent.replace(
  /("version"\s*:\s*")([^"]+)(")/,
  `$1${newVersion}$3`,
);

const updatedCargoTomlContent = cargoTomlContent.replace(
  /^version\s*=\s*"([^"]+)"/m,
  `version = "${newVersion}"`,
);

// 4. Write files
try {
  fs.writeFileSync(rootPackageJsonPath, updatedRootJsonContent, "utf8");
} catch (err) {
  console.error(`Error writing to root package.json: ${err.message}`);
  process.exit(1);
}

try {
  fs.writeFileSync(frontendPackageJsonPath, updatedFrontendJsonContent, "utf8");
} catch (err) {
  console.error(`Error writing to frontend package.json: ${err.message}`);
  process.exit(1);
}

try {
  fs.writeFileSync(cargoTomlPath, updatedCargoTomlContent, "utf8");
} catch (err) {
  console.error(`Error writing to Cargo.toml: ${err.message}`);
  process.exit(1);
}

// 5. Print summary
console.log("\nVersion bump successful!");
console.log(`- root package.json: ${oldRootVersion} → ${newVersion}`);
console.log(`- frontend/package.json: ${oldFrontendVersion} → ${newVersion}`);
console.log(
  `- frontend/src-tauri/Cargo.toml: ${oldCargoVersion} → ${newVersion}`,
);
console.log(
  "\nRemember to run 'cargo check' inside frontend/src-tauri/ to regenerate Cargo.lock",
);
