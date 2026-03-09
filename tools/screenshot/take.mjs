#!/usr/bin/env node

/**
 * Screenshot tool for QA visual inspection.
 * Uses puppeteer-core with system Chromium — no bundled browser.
 *
 * Usage:
 *   node take.mjs --url "http://localhost:5173" --viewport 1366x768
 *   node take.mjs --file "/path/to/activity.html" --viewport 1366x768
 *   node take.mjs --url "http://localhost:5173" --full-page --wait 3000
 */

import puppeteer from "puppeteer-core";
import { mkdirSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const EA_ROOT = resolve(__dirname, "../..");
const DEFAULT_OUTPUT_DIR = resolve(EA_ROOT, "temp/screenshots");
const CHROMIUM_PATH = "/usr/bin/chromium";

function parseArgs(argv) {
  const args = {
    url: null,
    file: null,
    viewport: "1366x768",
    output: null,
    wait: 2000,
    fullPage: false,
  };

  for (let i = 2; i < argv.length; i++) {
    switch (argv[i]) {
      case "--url":
        args.url = argv[++i];
        break;
      case "--file":
        args.file = argv[++i];
        break;
      case "--viewport":
        args.viewport = argv[++i];
        break;
      case "--output":
        args.output = argv[++i];
        break;
      case "--wait":
        args.wait = parseInt(argv[++i], 10);
        break;
      case "--full-page":
        args.fullPage = true;
        break;
      default:
        console.error(`Unknown argument: ${argv[i]}`);
        process.exit(1);
    }
  }

  if (!args.url && !args.file) {
    console.error("Error: --url or --file is required");
    process.exit(1);
  }
  if (args.url && args.file) {
    console.error("Error: --url and --file are mutually exclusive");
    process.exit(1);
  }

  return args;
}

function buildTargetUrl(args) {
  if (args.url) return args.url;
  const absPath = resolve(args.file);
  return `file://${absPath}`;
}

function buildOutputPath(args) {
  if (args.output) return resolve(args.output);

  if (!existsSync(DEFAULT_OUTPUT_DIR)) {
    mkdirSync(DEFAULT_OUTPUT_DIR, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  return resolve(DEFAULT_OUTPUT_DIR, `${timestamp}.png`);
}

function parseViewport(viewport) {
  const [w, h] = viewport.split("x").map(Number);
  if (!w || !h) {
    console.error(`Invalid viewport format: "${viewport}" — expected WxH (e.g. 1366x768)`);
    process.exit(1);
  }
  return { width: w, height: h };
}

async function main() {
  const args = parseArgs(process.argv);
  const targetUrl = buildTargetUrl(args);
  const outputPath = buildOutputPath(args);
  const { width, height } = parseViewport(args.viewport);

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: CHROMIUM_PATH,
      headless: true,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
      ],
    });

    const page = await browser.newPage();
    await page.setViewport({ width, height });
    await page.goto(targetUrl, { waitUntil: "networkidle2", timeout: 30000 });

    if (args.wait > 0) {
      await new Promise((r) => setTimeout(r, args.wait));
    }

    await page.screenshot({
      path: outputPath,
      fullPage: args.fullPage,
    });

    // Print the output path so calling agents can read the screenshot
    console.log(outputPath);
  } catch (err) {
    console.error(`Screenshot failed: ${err.message}`);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
}

main();
