# 🚀 Eliza Daemon Deployment Guide

## Quick Start

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/DevGruGold/eliza-daemon.git
cd eliza-daemon

# Run setup script
python setup.py

# Edit .env with your API keys
nano .env
```

### 2. Required API Keys
- **OpenAI**: Get from https://platform.openai.com/api-keys
- **Twitter**: Get from https://developer.twitter.com/
- **Supabase**: Get from https://supabase.com/
- **Discord Webhook**: Get from your Discord server settings

### 3. Run Eliza
```bash
python eliza_daemon.py
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f eliza-daemon
```

## Production Setup

### 1. Systemd Service
Create `/etc/systemd/system/eliza-daemon.service`:

```ini
[Unit]
Description=Eliza Daemon - XMRT DAO Agent
After=network.target

[Service]
Type=simple
User=eliza
WorkingDirectory=/opt/eliza-daemon
ExecStart=/usr/bin/python3 eliza_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start
```bash
sudo systemctl enable eliza-daemon.service
sudo systemctl start eliza-daemon.service
sudo systemctl status eliza-daemon.service
```

### 3. Monitor Logs
```bash
sudo journalctl -u eliza-daemon.service -f
```

## Configuration

### Supabase Setup
Create a table for Eliza's memory:

```sql
CREATE TABLE eliza_memory (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decision_data JSONB,
    reasoning TEXT,
    actions_taken INTEGER DEFAULT 0
);
```

### Environment Variables
All configuration is done via `.env` file:

```bash
TWITTER_BEARER=your_twitter_bearer_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
XMRT_API=https://api.xmrt.io/v1/miners
OPENAI_KEY=sk-your_openai_key
DISCORD_WEBHOOK=https://discord.com/api/webhooks/your_webhook
```

## Monitoring

### Health Check Endpoint
Eliza includes a simple health check endpoint (if you add web server):

```bash
curl http://localhost:8080/health
```

### Log Files
- Main log: `logs/eliza.log`
- Error log: `logs/error.log`

### Discord Notifications
Eliza will send status updates to your Discord channel including:
- Startup/shutdown notifications
- Decision summaries
- Error alerts

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all requirements are installed
2. **API Timeouts**: Check your internet connection and API limits
3. **Memory Issues**: Monitor Supabase connection and quotas
4. **Discord Not Working**: Verify webhook URL is correct

### Debug Mode
Set logging level to DEBUG in `eliza_daemon.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Scaling

### Multiple Instances
Run multiple Eliza instances for different tasks:

```bash
# Instance 1: Twitter monitoring
ELIZA_FOCUS=twitter python eliza_daemon.py

# Instance 2: Mining monitoring  
ELIZA_FOCUS=mining python eliza_daemon.py
```

### Load Balancing
Use nginx or similar for load balancing multiple Eliza instances.

## Security

### API Key Security
- Never commit API keys to git
- Use environment variables or secret management
- Rotate keys regularly

### Network Security  
- Run behind VPN if possible
- Use HTTPS for all API calls
- Monitor for unusual activity

## Support

For issues or questions:
- GitHub Issues: https://github.com/DevGruGold/eliza-daemon/issues
- Discord: XMRT DAO server
- Email: [Your contact email]
