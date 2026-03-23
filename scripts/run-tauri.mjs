import { accessSync, constants } from "node:fs";
import { delimiter, dirname, join, parse } from "node:path";
import { homedir } from "node:os";
import { spawn } from "node:child_process";

const isWindows = process.platform === "win32";
const executableSuffix = isWindows ? ".exe" : "";
const cargoCommand = isWindows ? "cargo.exe" : "cargo";
const rustcCommand = isWindows ? "rustc.exe" : "rustc";
const tauriCommand = isWindows ? "tauri.cmd" : "tauri";

function isExecutable(path) {
  try {
    accessSync(path, constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

function resolveCargoHomeBin() {
  const candidates = [
    process.env.CARGO_HOME ? join(process.env.CARGO_HOME, "bin") : null,
    join(homedir(), ".cargo", "bin"),
  ];

  for (const candidate of candidates) {
    if (candidate && isExecutable(join(candidate, cargoCommand))) {
      return candidate;
    }
  }

  return null;
}

function resolveLocalTauriBin() {
  let current = process.cwd();
  const { root } = parse(current);

  while (true) {
    const candidate = join(
      current,
      "node_modules",
      ".bin",
      isWindows ? "tauri.cmd" : "tauri",
    );

    if (isExecutable(candidate)) {
      return candidate;
    }

    if (current === root) {
      return tauriCommand;
    }

    current = dirname(current);
  }
}

function buildEnv() {
  const env = { ...process.env };
  const cargoBin = resolveCargoHomeBin();

  const pathEntries = unique([
    cargoBin,
    ...(env.PATH ?? "").split(delimiter),
  ]);

  env.PATH = pathEntries.join(delimiter);

  if (cargoBin) {
    env.CARGO = join(cargoBin, cargoCommand);

    const rustcPath = join(cargoBin, rustcCommand);
    if (isExecutable(rustcPath)) {
      env.RUSTC = rustcPath;
    }
  }

  return env;
}

const child = spawn(resolveLocalTauriBin(), process.argv.slice(2), {
  cwd: process.cwd(),
  env: buildEnv(),
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 1);
});

child.on("error", (error) => {
  const cargoBin = resolveCargoHomeBin();
  const details = cargoBin
    ? `Resolved Rust toolchain directory: ${dirname(join(cargoBin, cargoCommand))}`
    : "Rust toolchain was not found in $CARGO_HOME/bin or ~/.cargo/bin.";

  console.error(`Failed to launch Tauri CLI: ${error.message}`);
  console.error(details);
  process.exit(1);
});
