# OpenClaw Docker Setup Steps

1. **Created Directory**: Created `/home/dd/docker/openclaw` to hold the setup files.
2. **Cloned Repository**: Cloned the openclaw repository and downloaded setup scripts.
3. **Fixed Dockerfile**: Added `NODE_OPTIONS=--max-old-space-size=2048` to the `pnpm install` step in the Dockerfile to prevent the build from hanging due to memory limits.
4. **Built Image**: Successfully built the `openclaw:local` Docker image.
5. **Freed Disk Space**: Resolved a "No space left on device" error by pruning the Docker system to free up disk space.
6. **Configured docker-compose**: Added the `--allow-unconfigured` flag to the gateway command in `docker-compose.yml` to resolve a "Missing config" error.
7. **Started Services**: Started the `openclaw-gateway` service using `docker-compose up -d`.
8. **Verified Setup**: Checked the logs and verified the service is running and healthy by querying the `/health` endpoint.

## Next Steps (If needed)
- Configure authentication for the gateway if it needs to be exposed to public networks.
- Set up any required channels (e.g., WhatsApp, Telegram) using the `openclaw channels login` command.
- Configure the agent model and API keys in the `.env` file or via the CLI.
