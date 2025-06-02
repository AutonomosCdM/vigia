# GitHub Secrets Setup for Vigia

This guide explains how to configure GitHub Secrets for secure credential management in the Vigia project.

## Required Secrets

### 1. Twilio (WhatsApp Integration)
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `TWILIO_WHATSAPP_FROM`: Your Twilio WhatsApp number (format: whatsapp:+1234567890)

### 2. Anthropic (AI Processing)
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude

### 3. Slack (Notifications) - Optional
- `SLACK_BOT_TOKEN`: Your Slack bot token (xoxb-...)
- `SLACK_APP_TOKEN`: Your Slack app token (xapp-...)
- `SLACK_SIGNING_SECRET`: Your Slack signing secret

### 4. Supabase (Database)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key

## Setup Methods

### Method 1: Using GitHub CLI (Recommended)

1. **Install GitHub CLI** if not already installed:
   ```bash
   # macOS
   brew install gh
   
   # Ubuntu/Debian
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   ```

2. **Authenticate with GitHub**:
   ```bash
   gh auth login
   ```

3. **Run the setup script**:
   ```bash
   cd /path/to/vigia
   ./scripts/setup_github_secrets.sh
   ```

### Method 2: Manual Setup via GitHub Web

1. Go to https://github.com/AutonomosCdM/vigia/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret with its name and value

### Method 3: Using GitHub CLI Manually

```bash
# Set individual secrets
gh secret set TWILIO_ACCOUNT_SID --repo AutonomosCdM/vigia
gh secret set TWILIO_AUTH_TOKEN --repo AutonomosCdM/vigia
gh secret set ANTHROPIC_API_KEY --repo AutonomosCdM/vigia
# ... etc
```

## Using Secrets in GitHub Actions

Secrets are automatically available in GitHub Actions workflows:

```yaml
env:
  TWILIO_ACCOUNT_SID: ${{ secrets.TWILIO_ACCOUNT_SID }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Local Development

For local development, create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your credentials
```

**Important**: Never commit `.env` files with real credentials!

## Security Best Practices

1. **Rotate credentials regularly**
2. **Use different credentials for production/staging**
3. **Limit access to secrets** to only necessary team members
4. **Monitor secret usage** in GitHub Actions logs
5. **Never log or print secrets** in your code

## Troubleshooting

### Secret not available in workflow
- Ensure the secret name matches exactly (case-sensitive)
- Check that the workflow has access to secrets
- Verify the secret was saved to the correct repository

### Authentication errors
- Verify the secret values are correct
- Check for extra spaces or newlines in secret values
- Ensure API keys haven't expired

## Verification

After setup, you can verify secrets are configured:

```bash
# List all secrets (names only, not values)
gh secret list --repo AutonomosCdM/vigia
```

Expected output:
```
ANTHROPIC_API_KEY     Updated 2025-06-02
SLACK_APP_TOKEN       Updated 2025-06-02
SLACK_BOT_TOKEN       Updated 2025-06-02
SUPABASE_KEY          Updated 2025-06-02
SUPABASE_URL          Updated 2025-06-02
TWILIO_ACCOUNT_SID    Updated 2025-06-02
TWILIO_AUTH_TOKEN     Updated 2025-06-02
TWILIO_WHATSAPP_FROM  Updated 2025-06-02
```