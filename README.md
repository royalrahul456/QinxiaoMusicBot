# 🎵 Qinxiao Music (@QinxiaoMusicBot)

A complete, production-ready, feature-packed Telegram Music Bot built with **Pyrogram**, **PyTgCalls**, **FFmpeg**, and **SQLAlchemy**.

Designed for seamless, crystal-clear audio playback in Telegram Voice Chats with an interactive music player, smart queue engine, lyrics, favorites, premium subscriptions, group settings, and owner administration tools.

---

## 🌟 Key Features

### 🎧 Voice-Chat Playback & Audio Processing
- **High-Quality Audio Streaming**: Stream music directly to Telegram Group/Channel Voice Chats using PyTgCalls.
- **FFmpeg Real-Time Filter Engine**: Real-time Volume Adjustment (0-200%), Audio Bitrate Selection (`64k` to `320k`), Equalizer Presets (`flat`, `rock`, `pop`, `jazz`, `classical`, `bass`), Bass Boost Level (1-10), and Loudnorm Volume Normalization.
- **24/7 Presence**: Keep the bot connected in voice chats continuously.
- **Auto-Leave**: Automatically disconnect when voice chat remains empty after a configurable delay.

### 📋 Smart Queue & Playback Modes
- **Per-Group Smart Queues**: Dedicated thread-safe queue for every group with configurable queue size limits.
- **Repeat & Loop Modes**: Off, Single Track Loop (`/loop`), or Queue Loop (`/loopqueue`).
- **Autoplay Recommendations**: Automatically fetch and play similar songs when the queue finishes.
- **Skip Voting**: Democratic skip voting system with customizable required percentage and admin bypass.
- **Duplicate Protection**: Prevents adding duplicate songs into the queue.

### 🔍 Multi-Provider Music & Lyrics Search
- **YouTube Integration**: Search and extract audio streams via `yt-dlp`.
- **Spotify Metadata Search**: Search Spotify metadata for tracks, albums, and playlists.
- **SoundCloud Support**: Extract and play tracks from SoundCloud.
- **Synced & Plain Lyrics**: Multi-source lyrics search with LRC synchronized timestamp parser.
- **Inline Music Search**: Search and share songs inline via `@QinxiaoMusicBot`.

### 👑 Premium & Owner Management
- **Multi-Tier Premium System**: Standard, Pro, and Ultimate plans with expiration tracking, higher queue limits, and 24/7 access.
- **Key Generation & Activation**: Secure activation key generator (`/genkey`), user activation (`/activate`), and revocation (`/revokekey`).
- **Permission Hierarchy**: Strictly enforced role validation (`OWNER` ➔ `SUDO` ➔ `ADMIN` ➔ `USER`).
- **Owner Suite**: Global broadcast, system metrics (`/botstats`), active voice chat manager (`/activevc`), leave all (`/leaveall`), maintenance mode (`/maintenance`), restart (`/restart`), latency test (`/speedtest`), and Sudo management.

---

## 📁 Project Architecture

```
QinxiaoMusicBot/
├── app/
│   ├── main.py                  # Application entry point & lifecycle bootstrap
│   ├── config/                  # Environment & Pydantic settings management
│   ├── bot/                     # Pyrogram client factory & bot instance
│   ├── database/                # SQLAlchemy async engine, session, & table initialization
│   ├── models/                  # ORM Models (User, Chat, Song, Favorite, History, Premium, Sudo, Stats)
│   ├── repositories/            # Data Access Layer (CRUD abstractions)
│   ├── cache/                   # In-memory & Redis cache manager
│   ├── permissions/             # Permission hierarchy & role checker
│   ├── middleware/              # Anti-spam rate limiting & maintenance mode
│   ├── providers/               # Music providers (YouTube, Spotify metadata, SoundCloud)
│   ├── audio/                   # FFmpeg filter builder, quality profiles, & audio processor
│   ├── player/                  # VC client, queue manager, vote-skip tracker, UI, & playback manager
│   ├── lyrics/                  # Lyrics provider & LRC synced parser
│   ├── handlers/                # Pyrogram command & inline query handlers
│   ├── callbacks/               # Interactive inline player & settings callback handlers
│   ├── premium/                 # Premium key generator & plan manager
│   ├── statistics/              # System & bot usage metrics tracker
│   └── utils/                   # Formatting, time, & validation utilities
├── tests/                       # Complete Pytest test suite
├── .env.example                 # Environment template file
├── requirements.txt             # Project dependencies
├── pytest.ini                   # Pytest configuration
└── README.md                    # Documentation
```

---

## 🚀 Setup & Installation

### 1. Requirements
- **Python**: 3.10 or higher
- **FFmpeg**: Installed on system and added to PATH (or configured via `FFMPEG_PATH`)
- **Telegram API Credentials**: `API_ID` & `API_HASH` from [my.telegram.org](https://my.telegram.org)
- **Telegram Bot Token**: Obtained from [@BotFather](https://t.me/BotFather) for `@QinxiaoMusicBot`

### 2. Clone & Install Dependencies
```bash
git clone https://github.com/yourusername/QinxiaoMusicBot.git
cd QinxiaoMusicBot

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyZ
API_ID=12345678
API_HASH=0123456789abcdef0123456789abcdef
OWNER_ID=123456789
DATABASE_URL=sqlite+aiosqlite:///qinxiao_music.db
```

### 4. Run the Bot
```bash
python -m app.main
```

### 5. Running Tests
```bash
pytest -v
```

---

## 📜 Commands Reference

### 🎵 Music Commands
| Command | Description |
|---|---|
| `/play <query/URL>` | Search and play music in voice chat |
| `/search <query>` | Interactive search for songs |
| `/pause` | Pause current playback |
| `/resume` | Resume paused playback |
| `/skip` | Skip current song (or register vote) |
| `/stop` | Stop playback and clear queue |
| `/replay` | Restart current song |
| `/seek <seconds>` | Jump to timestamp |
| `/volume <0-200>` | Change playback volume |
| `/mute` / `/unmute` | Mute or unmute audio |

### 📋 Queue Commands
| Command | Description |
|---|---|
| `/queue` | Display current queue |
| `/nowplaying` | Show currently playing track info |
| `/shuffle` | Shuffle queued tracks |
| `/clear` | Clear all queued songs |
| `/loop` | Toggle single-track loop |
| `/loopqueue` | Toggle queue loop |
| `/autoplay` | Toggle automatic similar song recommendations |

### 🎛 Audio & Group Settings
| Command | Description |
|---|---|
| `/quality <low/med/high>` | Set audio quality profile |
| `/bitrate <64k-320k>` | Set stream bitrate |
| `/equalizer <preset>` | Apply EQ preset (`rock`, `pop`, `jazz`, etc.) |
| `/bassboost <0-10>` | Set bass boost level |
| `/normalizer` | Toggle volume normalization |
| `/audioinfo` | View detailed audio statistics |
| `/247` | Toggle 24/7 voice chat presence |
| `/autoleave` | Toggle automatic leave on empty VC |
| `/player` | Open interactive player UI |

### 👑 Premium & Owner Commands
| Command | Permission | Description |
|---|---|---|
| `/premium` | User | Check premium subscription status |
| `/plans` | User | View available premium plans |
| `/activate <key>` | User | Redeem premium activation key |
| `/genkey <plan> <days>`| Owner | Generate a new premium key |
| `/revokekey <key>` | Owner | Revoke an existing key |
| `/broadcast` | Owner | Send global announcement |
| `/botstats` | Sudo/Owner | View full system resource metrics |
| `/activevc` | Sudo/Owner | List active voice chats |
| `/leaveall` | Owner | Disconnect bot from all voice chats |
| `/maintenance` | Owner | Toggle maintenance mode |
| `/restart` | Owner | Restart bot application |
| `/addsudo` / `/delsudo` | Owner | Manage Sudo administrators |

---

## 🛡 License & Identity
Developed for **Qinxiao Music** (`@QinxiaoMusicBot`).
All rights reserved.
