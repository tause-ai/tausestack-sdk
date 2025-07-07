#!/bin/bash

# Supabase Production Setup Script
set -e

DOMAIN_NAME=${1:-"tausestack.dev"}
SUPABASE_PROJECT_ID=${2}
SUPABASE_SERVICE_KEY=${3}

if [ -z "$SUPABASE_PROJECT_ID" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo "❌ Error: Missing Supabase credentials"
    echo "Usage: $0 <domain> <project_id> <service_key>"
    exit 1
fi

echo "🔐 Setting up Supabase for production domain: $DOMAIN_NAME"

# Configure Supabase CLI if not already done
if ! command -v supabase &> /dev/null; then
    echo "📦 Installing Supabase CLI..."
    npm install -g supabase
fi

# Login to Supabase (requires interactive token)
echo "🔑 Please login to Supabase CLI if not already logged in:"
supabase login || true

# Configure allowed origins for production
echo "🌐 Configuring CORS origins..."
cat > /tmp/supabase-config.sql << EOF
-- Update auth configuration for production
UPDATE auth.config 
SET 
    site_url = 'https://$DOMAIN_NAME',
    additional_redirect_urls = ARRAY[
        'https://$DOMAIN_NAME',
        'https://app.$DOMAIN_NAME',
        'https://api.$DOMAIN_NAME'
    ]
WHERE id = 1;

-- Configure JWT settings
UPDATE auth.config 
SET 
    jwt_exp = 3600,
    refresh_token_rotation_enabled = true,
    security_update_password_require_reauthentication = true
WHERE id = 1;

-- Add production RLS policies if needed
-- (These should already exist from development setup)
EOF

# Apply configuration
echo "📝 Applying Supabase configuration..."
# Note: This would need to be run via Supabase dashboard or API
echo "⚠️  Please manually apply the following configuration in your Supabase dashboard:"
echo "---"
cat /tmp/supabase-config.sql
echo "---"

# Create production environment file
echo "📄 Creating production environment configuration..."
cat > .env.production.supabase << EOF
# Supabase Production Configuration
NEXT_PUBLIC_SUPABASE_URL=https://$SUPABASE_PROJECT_ID.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<YOUR_ANON_KEY>

# Production URLs
NEXT_PUBLIC_APP_URL=https://$DOMAIN_NAME
NEXT_PUBLIC_API_URL=https://api.$DOMAIN_NAME

# Site configuration
NEXT_PUBLIC_SITE_URL=https://$DOMAIN_NAME
EOF

echo "✅ Supabase production setup completed!"
echo "📋 Next steps:"
echo "1. Update your .env.production with the correct SUPABASE_ANON_KEY"
echo "2. Configure the CORS origins in your Supabase dashboard"
echo "3. Test authentication with the production domain"

# Clean up
rm -f /tmp/supabase-config.sql 