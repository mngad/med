# Markdown Editor - python Desktop App

Create a cross-platform desktop application using **python** — a modern, distraction-free Markdown editor with a side-by-side live preview and native system integration.

## Core Features

### Editor & Preview
- **Split-screen layout**: A side-by-side view with a text editor on the left and a rendered preview on the right.
- **Synchronized scrolling**: Scrolling the editor should automatically scroll the preview to the corresponding position.
- **Live Rendering**: The preview should update in real-time as the user types.

### Layout Modes
- **Split View**: Default side-by-side mode.
- **Preview Only**: A toggle to completely hide the editor panel for a clean reading experience.
- **Focus Mode**: A toggle to hide the preview for maximum writing focus.

### Native File System Integration
- **Open File**: Use whatever you think best dialog API to open `.md` files from the local disk.
- **Save / Save As**: Implement native "Save" and "Save As" functionality.
- **Title Bar Integration**: Display the current filename in the window title bar, with an asterisk (*) indicating unsaved changes.

### Toolbar
- A minimal toolbar at the top with buttons for formatting: `B` (Bold), `I` (Italic), `H` (Heading), `List`, `Link`, `Code`.
- Keyboard shortcuts: `Cmd/Ctrl + S` (Save), `Cmd/Ctrl + O` (Open), `Cmd/Ctrl + N` (New).

### Design Requirements
- **Premium Desktop Look**: Use a native-feeling design with glassmorphism or a clean sidebar.
- **Color Themes**: Support Light and Dark modes, preferably syncing with the OS theme by default.
- **Customizable Typography**: Allow users to choose between a few curated fonts for the editor and preview.

## Technical Constraints
- **Packaging**: Ensure the app can be built for macOS, Windows, and Linux.

