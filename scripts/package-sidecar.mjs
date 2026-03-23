import { chmodSync, copyFileSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const inferenceRoot = join(root, "services", "inference");
const desktopBinaryDir = join(root, "apps", "desktop", "src-tauri", "binaries");
const buildRoot = join(inferenceRoot, "build", "sidecar");
const packagedBinaryName = process.platform === "win32"
  ? "home-voice-studio-inference.exe"
  : "home-voice-studio-inference";

function resolveTargetTriple() {
  const explicit = process.env.TAURI_ENV_TARGET_TRIPLE ?? process.env.HVS_TARGET_TRIPLE;
  if (explicit) {
    return explicit;
  }

  try {
    const result = run("rustc", ["-vV"], { stdio: "pipe" });
    const output = String(result.stdout ?? "");
    const hostLine = output
      .split("\n")
      .find((line) => line.startsWith("host:"));
    return hostLine?.split(":")[1]?.trim() || null;
  } catch {
    return null;
  }
}

function targetBinaryName() {
  const triple = resolveTargetTriple();
  if (!triple) {
    return null;
  }
  return process.platform === "win32"
    ? `home-voice-studio-inference-${triple}.exe`
    : `home-voice-studio-inference-${triple}`;
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? root,
    stdio: options.stdio ?? "inherit",
    env: options.env ?? process.env,
  });

  if (result.error) {
    throw result.error;
  }

  return result;
}

function pythonCandidates() {
  return [
    { command: process.env.HVS_PYTHON, args: [] },
    { command: process.env.HOME_VOICE_STUDIO_PYTHON, args: [] },
    { command: "python3", args: [] },
    { command: "python", args: [] },
    { command: "py", args: ["-3"] },
  ].filter((candidate) => typeof candidate.command === "string" && candidate.command.length > 0);
}

function resolvePackager() {
  for (const candidate of pythonCandidates()) {
    try {
      const probe = run(candidate.command, [...candidate.args, "-c", "import fastapi, uvicorn, PyInstaller"], {
        cwd: inferenceRoot,
        stdio: "ignore",
      });
      if (probe.status === 0) {
        return candidate;
      }
    } catch {
      continue;
    }
  }

  return null;
}

function resolveExplicitBinary() {
  for (const key of ["HVS_SIDECAR_BIN", "HOME_VOICE_STUDIO_SIDECAR_BIN"]) {
    const value = process.env[key];
    if (value && existsSync(value)) {
      return resolve(value);
    }
  }

  return null;
}

function ensureOutputDir() {
  mkdirSync(desktopBinaryDir, { recursive: true });
}

function stageBinaryVariants(source) {
  ensureOutputDir();
  const outputs = [join(desktopBinaryDir, packagedBinaryName)];
  const targetName = targetBinaryName();
  if (targetName) {
    outputs.push(join(desktopBinaryDir, targetName));
  }

  for (const destination of outputs) {
    if (resolve(source) !== resolve(destination)) {
      rmSync(destination, { force: true });
      copyFileSync(source, destination);
    }
    if (process.platform !== "win32") {
      chmodSync(destination, 0o755);
    }
  }

  return outputs;
}

function stageExistingBinary(source) {
  const outputs = stageBinaryVariants(source);
  return outputs[outputs.length - 1];
}

function buildWithPyInstaller(candidate) {
  mkdirSync(buildRoot, { recursive: true });
  ensureOutputDir();
  const cacheRoot = join(buildRoot, "cache");
  const pyinstallerConfigDir = join(cacheRoot, "pyinstaller");
  const mplConfigDir = join(cacheRoot, "matplotlib");
  const xdgCacheHome = join(cacheRoot, "xdg");
  mkdirSync(pyinstallerConfigDir, { recursive: true });
  mkdirSync(mplConfigDir, { recursive: true });
  mkdirSync(xdgCacheHome, { recursive: true });

  const args = [
    ...candidate.args,
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--name",
    "home-voice-studio-inference",
    "--distpath",
    desktopBinaryDir,
    "--workpath",
    join(buildRoot, "work"),
    "--specpath",
    join(buildRoot, "spec"),
    "--paths",
    inferenceRoot,
    "app/cli.py",
  ];

  const result = run(candidate.command, args, {
    cwd: inferenceRoot,
    env: {
      ...process.env,
      PYINSTALLER_CONFIG_DIR: pyinstallerConfigDir,
      MPLCONFIGDIR: mplConfigDir,
      XDG_CACHE_HOME: xdgCacheHome,
    },
  });
  if (result.status !== 0) {
    return null;
  }

  const destination = join(desktopBinaryDir, packagedBinaryName);
  if (!existsSync(destination)) {
    throw new Error(`PyInstaller finished but did not produce ${destination}`);
  }

  const outputs = stageBinaryVariants(destination);
  return outputs[outputs.length - 1];
}

function prepare() {
  try {
    return stageExistingBinary(check());
  } catch {
    // Keep going and build or copy a sidecar when one is not already staged.
  }

  const explicitBinary = resolveExplicitBinary();
  if (explicitBinary) {
    return stageExistingBinary(explicitBinary);
  }

  const packager = resolvePackager();
  if (!packager) {
    throw new Error(
      "PyInstaller is not installed and no explicit sidecar binary was provided. Install the packaging extra with `pip install -e \"services/inference[package]\"` or set HVS_SIDECAR_BIN to an existing home-voice-studio-inference executable.",
    );
  }

  const destination = buildWithPyInstaller(packager);
  if (!destination) {
    throw new Error("PyInstaller failed to build the bundled sidecar executable.");
  }

  return destination;
}

function check() {
  const targetName = targetBinaryName();
  const candidates = [
    targetName ? join(desktopBinaryDir, targetName) : null,
    join(desktopBinaryDir, packagedBinaryName),
  ].filter(Boolean);

  const destination = candidates.find((candidate) => existsSync(candidate));
  if (!destination) {
    throw new Error(
      `Missing bundled sidecar executable under ${desktopBinaryDir}. Run \`npm run package:sidecar\` before packaging the desktop app.`,
    );
  }

  return destination;
}

function main(argv) {
  const command = argv[2] ?? "prepare";

  try {
    if (command === "prepare") {
      const destination = prepare();
      console.log(`Packaged sidecar staged at ${destination}`);
      return 0;
    }

    if (command === "check") {
      const destination = check();
      console.log(`Bundled sidecar present at ${destination}`);
      return 0;
    }

    console.error(`Unknown command: ${command}`);
    return 2;
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    return 1;
  }
}

process.exitCode = main(process.argv);
