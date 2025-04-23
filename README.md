# Bitbucket Branch Creator

🚀 An async Python script to **automatically create a new branch** from an existing one across **all repositories** in a Bitbucket workspace.

This tool is especially useful for:
- Managing bulk branch operations
- Automating dev environment setups
- Repository hygiene and audits

---

## 📌 Features

- ✅ Async implementation using `aiohttp` for high performance
- ✅ Handles pagination to fetch all repositories
- ✅ Creates a new branch from a specified source branch
- ✅ Logs all repository names to a text file
- ✅ Handles errors and branch conflicts gracefully

---

## 🛠️ Requirements

Install dependencies with:

```bash
pip install aiohttp aiofiles
