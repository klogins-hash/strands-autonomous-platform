# Setup Guide - Strands Autonomous Platform

## Quick Setup (Recommended)

Run the automated setup script:

```bash
./scripts/setup-environment.sh
```

This will:
1. Install Docker and Colima (if needed)
2. Start Docker runtime
3. Install Python dependencies
4. Create .env file
5. Start all services (PostgreSQL, Redis, MinIO)

---

## Manual Setup

### 1. Install Docker (without Docker Desktop)

**Option A: Automated**
```bash
./scripts/install-docker.sh
```

**Option B: Manual**
```bash
# Install Docker and Colima via Homebrew
brew install docker docker-compose colima

# Start Colima (Docker runtime)
colima start --cpu 4 --memory 8 --disk 50
```

### 2. Verify Docker Installation

```bash
docker version
docker ps
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required API keys:
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `OPENAI_API_KEY` - Get from https://platform.openai.com/
- `E2B_API_KEY` - Get from https://e2b.dev/

### 5. Start Services

```bash
./scripts/start-services.sh
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)

### 6. Run the Platform

```bash
python main.py
```

---

## Docker Management with Colima

### Start Docker
```bash
colima start
```

### Stop Docker
```bash
colima stop
```

### Check Status
```bash
colima status
docker ps
```

### Restart Docker
```bash
colima restart
```

### Configure Resources
```bash
# Adjust CPU, memory, and disk
colima start --cpu 4 --memory 8 --disk 50
```

---

## Service Management

### Start Services
```bash
./scripts/start-services.sh
```

### Stop Services
```bash
./scripts/stop-services.sh
```

### View Logs
```bash
docker-compose logs -f
```

### View Specific Service Logs
```bash
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f minio
```

### Restart Services
```bash
docker-compose restart
```

### Remove All Data (Clean Slate)
```bash
docker-compose down -v
```

---

## Access Services

### PostgreSQL
```bash
# Connection string
postgresql://strands:strands_password@localhost:5432/strands_platform

# Connect via psql
docker exec -it strands-postgres psql -U strands -d strands_platform
```

### Redis
```bash
# Connect via redis-cli
docker exec -it strands-redis redis-cli
```

### MinIO

**Web Console:** http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

**API Endpoint:** http://localhost:9000

---

## Troubleshooting

### Docker Not Running
```bash
# Check Colima status
colima status

# Start Colima
colima start

# Check Docker
docker info
```

### Port Already in Use
```bash
# Find what's using the port
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9000  # MinIO

# Kill the process
kill -9 <PID>
```

### Services Not Starting
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Complete reset
docker-compose down -v
docker-compose up -d
```

### Colima Issues
```bash
# Delete and recreate
colima delete
colima start --cpu 4 --memory 8 --disk 50
```

### Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## Development Workflow

1. **Start services** (once per session)
   ```bash
   ./scripts/start-services.sh
   ```

2. **Activate virtual environment** (if using)
   ```bash
   source venv/bin/activate
   ```

3. **Run the platform**
   ```bash
   python main.py
   ```

4. **Stop services** (when done)
   ```bash
   ./scripts/stop-services.sh
   ```

---

## System Requirements

- **OS:** macOS (Intel or Apple Silicon)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 10GB free space minimum
- **Python:** 3.11 or higher
- **Homebrew:** Latest version

---

## Uninstall

### Remove Services
```bash
docker-compose down -v
```

### Remove Docker/Colima
```bash
colima delete
brew uninstall colima docker docker-compose
```

### Remove Python Environment
```bash
deactivate  # If in virtual environment
rm -rf venv
```

---

## Next Steps

After setup is complete:

1. ✅ Verify all services are running
2. ✅ Check API keys in `.env`
3. ✅ Run `python main.py` to start the autonomous agent team
4. ✅ Access MinIO console at http://localhost:9001
5. ✅ Monitor agent activity in real-time

For more information, see [README.md](README.md)
