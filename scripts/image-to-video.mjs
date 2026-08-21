#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const API_BASE = 'https://api.dev.runwayml.com/v1';
const API_VERSION = '2024-11-06';
const TERMINAL_STATUSES = new Set(['SUCCEEDED', 'FAILED', 'CANCELLED']);

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith('--')) continue;
    const key = token.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith('--')) {
      args[key] = true;
    } else {
      args[key] = value;
      index += 1;
    }
  }
  return args;
}

function usage() {
  console.error(`Usage:
  npm run video:generate -- \\
    --image ./path/to/source.png \\
    --prompt "Subtle natural movement, slow handheld camera drift" \\
    [--output ./output/video.mp4] \\
    [--model gen4.5] \\
    [--ratio 720:1280] \\
    [--duration 5] \\
    [--seed 1234]

Required environment variable:
  RUNWAYML_API_SECRET
`);
}

function mimeTypeFor(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === '.png') return 'image/png';
  if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
  if (ext === '.webp') return 'image/webp';
  throw new Error(`Unsupported image type: ${ext || '(none)'}. Use PNG, JPEG or WebP.`);
}

async function imageToDataUri(filePath) {
  const file = await readFile(filePath);
  const maxBytes = 5 * 1024 * 1024;
  if (file.byteLength > maxBytes) {
    throw new Error(`Image is ${(file.byteLength / 1024 / 1024).toFixed(2)}MB. Data URI inputs must be 5MB or smaller.`);
  }
  return `data:${mimeTypeFor(filePath)};base64,${file.toString('base64')}`;
}

async function runwayRequest(endpoint, options = {}) {
  const apiKey = process.env.RUNWAYML_API_SECRET;
  if (!apiKey) throw new Error('RUNWAYML_API_SECRET is not set.');

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'X-Runway-Version': API_VERSION,
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  });

  const text = await response.text();
  let payload;
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { raw: text };
  }

  if (!response.ok) {
    const details = payload?.error || payload?.message || payload?.raw || response.statusText;
    throw new Error(`Runway API ${response.status}: ${typeof details === 'string' ? details : JSON.stringify(details)}`);
  }

  return payload;
}

async function createTask({ image, prompt, model, ratio, duration, seed }) {
  const body = {
    model,
    promptImage: image,
    promptText: prompt,
    ratio,
    duration,
  };
  if (seed !== undefined) body.seed = seed;

  return runwayRequest('/image_to_video', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

async function waitForTask(taskId, pollMs = 5000) {
  while (true) {
    const task = await runwayRequest(`/tasks/${taskId}`);
    const status = task.status || 'UNKNOWN';
    process.stdout.write(`\rRunway task ${taskId}: ${status.padEnd(12)}`);

    if (TERMINAL_STATUSES.has(status)) {
      process.stdout.write('\n');
      if (status !== 'SUCCEEDED') {
        throw new Error(`Generation ${status.toLowerCase()}: ${JSON.stringify(task.failure || task)}`);
      }
      return task;
    }

    await new Promise((resolve) => setTimeout(resolve, pollMs));
  }
}

async function downloadVideo(url, outputPath) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Video download failed: HTTP ${response.status}`);
  const buffer = Buffer.from(await response.arrayBuffer());
  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeFile(outputPath, buffer);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.image || !args.prompt) {
    usage();
    process.exitCode = 2;
    return;
  }

  const duration = Number(args.duration ?? 5);
  if (!Number.isInteger(duration) || duration < 2 || duration > 10) {
    throw new Error('--duration must be an integer from 2 to 10.');
  }

  const seed = args.seed === undefined ? undefined : Number(args.seed);
  if (seed !== undefined && (!Number.isInteger(seed) || seed < 0 || seed > 4294967295)) {
    throw new Error('--seed must be an integer from 0 to 4294967295.');
  }

  const inputPath = path.resolve(args.image);
  const outputPath = path.resolve(
    args.output ?? path.join('output', 'image-to-video', `${path.parse(inputPath).name}-${Date.now()}.mp4`),
  );

  const promptImage = await imageToDataUri(inputPath);
  const task = await createTask({
    image: promptImage,
    prompt: args.prompt,
    model: args.model ?? 'gen4.5',
    ratio: args.ratio ?? '720:1280',
    duration,
    seed,
  });

  if (!task.id) throw new Error(`Runway did not return a task ID: ${JSON.stringify(task)}`);
  console.log(`Created Runway task: ${task.id}`);

  const completed = await waitForTask(task.id);
  const videoUrl = completed.output?.[0];
  if (!videoUrl) throw new Error(`Task succeeded without an output URL: ${JSON.stringify(completed)}`);

  await downloadVideo(videoUrl, outputPath);
  console.log(`Saved video: ${outputPath}`);
}

main().catch((error) => {
  console.error(`\nImage-to-video failed: ${error.message}`);
  process.exitCode = 1;
});
