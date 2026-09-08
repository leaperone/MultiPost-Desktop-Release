# MultiPost Desktop — English Edition

<p align="center">
  <strong>One-click publishing to 50+ social media platforms. Local-first. Privacy-focused.</strong>
</p>

<p align="center">
  <a href="https://github.com/leaperone/MultiPost-Desktop-Release/releases/latest">
    <img src="https://img.shields.io/github/v/release/leaperone/MultiPost-Desktop-Release?style=flat-square" alt="Latest Release">
  </a>
  <img src="https://img.shields.io/github/license/leaperone/MultiPost-Desktop-Release?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey?style=flat-square" alt="Platforms">
</p>

---

## What is MultiPost?

MultiPost is a **free, open-source desktop application** for content creators who need to publish across multiple social media platforms simultaneously. Instead of logging into each platform one by one and pasting content manually, MultiPost lets you compose once and publish everywhere — all from a single, local-first desktop app.

This is the **English edition**, maintained as a community fork of the original [MultiPost](https://github.com/leaperone/MultiPost-Desktop-Release) project by [LEAPERone](https://github.com/leaperone).

---

## Download

Download the latest version for your platform from the [Releases](https://github.com/leaperone/MultiPost-Desktop-Release/releases) page, or grab the macOS `.app` bundle directly from this repo's [Releases](../../releases).

### Supported Platforms

| Platform | Architecture | File Type |
|----------|-------------|-----------|
| macOS | Apple Silicon (arm64) | `.dmg` / `.app` |
| macOS | Intel (x64) | `.dmg` / `.app` |
| Windows | x64 | `.exe` |
| Linux | x64 | `.AppImage`, `.deb` |

---

## Installation

### macOS

1. Download the `.dmg` file (or `.app` bundle) for your architecture
2. Open the `.dmg` file
3. Drag **MultiPost** to your Applications folder
4. On first launch, right-click → Open (to bypass Gatekeeper if needed)

### Windows

1. Download the `.exe` installer
2. Run the installer
3. Follow the installation wizard

### Linux

**AppImage:**
```bash
chmod +x MultiPost-*.AppImage
./MultiPost-*.AppImage
```

**Debian/Ubuntu:**
```bash
sudo dpkg -i multipost-desktop_*.deb
```

---

## Features

- **50+ platforms** — Weibo, Bilibili, Xiaohongshu, Douyin, Twitter/X, Facebook, LinkedIn, and more
- **Multi-format publishing** — Post text, images, videos, articles, and podcasts
- **Session isolation** — Each platform account runs in its own isolated browser session
- **Local-first** — All data stays on your machine. No cloud sync, no tracking.
- **One-click publish** — Select platforms, compose once, publish everywhere
- **Batch operations** — Check login status, detect issues, and manage accounts in bulk
- **MCP integration** — Built-in Model Context Protocol support for AI-assisted workflows

---

## Screenshots

> *Screenshots coming soon. Contributions welcome!*

---

## Building from Source

This English edition is built on top of the original MultiPost source code. If you want to build from source:

### Prerequisites

- [Node.js](https://nodejs.org/) >= 18.0.0
- [pnpm](https://pnpm.io/) (enforced by preinstall hook)
- macOS: Xcode Command Line Tools

### Setup

```bash
# Clone the repository
git clone https://github.com/RealRaylaxen/MultiPost-English.git
cd MultiPost-English

# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for macOS
pnpm build:mac

# Build for Windows
pnpm build:win

# Run linter
pnpm lint
```

### Project Structure

```
src/
├── main/              # Electron main process
│   ├── browser/       # BrowserView management
│   ├── ipc/           # IPC handlers
│   └── platforms/     # Platform adapters (publishing scripts)
├── renderer/          # React renderer process
├── preload/           # Preload scripts (API bridge)
└── shared/            # Shared types and constants
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Electron |
| Bundler | Vite |
| UI | React + TypeScript |
| Styling | Tailwind CSS |
| State | Zustand |
| Components | Radix UI, shadcn-style |
| Animations | Framer Motion |
| Validation | Zod |
| Database | better-sqlite3 |

---

## Design System

MultiPost follows a **minimalist black & white** design language:

- Only Tailwind semantic colors (`bg-background`, `text-foreground`, `text-muted-foreground`)
- **The One Red Rule** — The only hue is `text-destructive` (failure/destructive actions only)
- **Flat by default** — No shadows on static surfaces; only floating layers (popovers, dialogs) may cast shadows
- Borders: Only `border` class, never `border-gray-xxx`
- Font weights: 400/500/600 only — no `font-bold`
- Destructive operations must go through a confirmation dialog

---

## Contributing

Contributions are welcome! This English edition is community-maintained.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `chore:` — Maintenance tasks
- `refactor:` — Code restructuring without behavior change

---

## Credits

This English edition is built on the incredible work by the [LEAPERone](https://github.com/leaperone) team. All credit for the original application goes to them.

- **Original Project**: [MultiPost-Desktop-Release](https://github.com/leaperone/MultiPost-Desktop-Release)
- **Original Author**: [leaperone](https://github.com/leaperone)
- **English Edition Maintainer**: [RealRaylaxen](https://github.com/RealRaylaxen) (Mohammed Ashraf Morssy)

---

## License

[MIT License](LICENSE) — See the original repository for full license details.

---

## Support

- **Bug Reports**: [Open an Issue](../../issues)
- **Discussions**: [Start a Discussion](../../discussions)
- **Original Issues**: [MultiPost-Desktop Issues](https://github.com/leaperone/MultiPost-Desktop/issues)

---

<p align="center">
  Made with care for the global creator community 🌍
</p>
