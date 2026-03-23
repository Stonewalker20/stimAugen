import { expect, test } from "@playwright/test";

const baseUrl = process.env.HVS_E2E_URL ?? "http://127.0.0.1:1420";
const runEnabled = process.env.HVS_E2E_RUN === "1";

function wavFile(name: string, frequency: number): { name: string; mimeType: string; buffer: Buffer } {
  const sampleRate = 16000;
  const durationSeconds = 0.5;
  const totalFrames = Math.floor(sampleRate * durationSeconds);
  const bytesPerSample = 2;
  const data = Buffer.alloc(totalFrames * bytesPerSample);
  for (let index = 0; index < totalFrames; index += 1) {
    const t = index / sampleRate;
    const amplitude = Math.sin(2 * Math.PI * frequency * t) * 12000;
    data.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(amplitude))), index * bytesPerSample);
  }

  const header = Buffer.alloc(44);
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + data.length, 4);
  header.write("WAVE", 8);
  header.write("fmt ", 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(sampleRate * bytesPerSample, 28);
  header.writeUInt16LE(bytesPerSample, 32);
  header.writeUInt16LE(16, 34);
  header.write("data", 36);
  header.writeUInt32LE(data.length, 40);

  return {
    name,
    mimeType: "audio/wav",
    buffer: Buffer.concat([header, data]),
  };
}

test.describe("Home Voice Studio smoke journeys", () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!runEnabled, "Set HVS_E2E_RUN=1 and HVS_E2E_URL to execute the smoke suite.");
    await page.goto(baseUrl);
  });

  test("Speak Text", async ({ page }) => {
    await page.getByRole("tab", { name: "Speak Text" }).click();
    await page.getByLabel("Text").fill("Hello from Home Voice Studio");
    await page.getByRole("button", { name: /generate/i }).click();
    await expect(page.getByText(/preview/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /export/i })).toBeVisible();
  });

  test("Change Voice", async ({ page }) => {
    await page.getByRole("tab", { name: "Change Voice" }).click();
    await page.getByLabel("Input Audio").setInputFiles(wavFile("sample-speech.wav", 220));
    await page.getByLabel("Voice").selectOption({ label: "Warm Narrator" });
    await page.getByRole("button", { name: /convert/i }).click();
    await expect(page.getByText(/before/i)).toBeVisible();
    await expect(page.getByText(/after/i)).toBeVisible();
  });

  test("Clean Recording", async ({ page }) => {
    await page.getByRole("tab", { name: "Clean Recording" }).click();
    await page.getByLabel("Input Audio").setInputFiles(wavFile("sample-noisy.wav", 180));
    await page.getByLabel("Cleanup Level").fill("0.7");
    await page.getByRole("button", { name: /clean/i }).click();
    await expect(page.getByText(/cleaned/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /export/i })).toBeVisible();
  });
});
