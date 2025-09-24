#!/bin/bash
set -e

# Deployment script for AI Mentor Platform
# Usage: ./scripts/deploy.sh [staging|production]

ENVIRONMENT=${1:-staging}
DOMAIN=${2:-your-domain.com}

echo "🚀 Deploying AI Mentor Platform - $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not installed${NC}"
        exit 1
    fi
    
    if [ ! -f ".env.production" ]; then
        echo -e "${YELLOW}⚠️  .env.production not found. Creating from template...${NC}"
        cp .env.production.example .env.production
        echo -e "${RED}❗ Please edit .env.production with your values${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All requirements met${NC}"
}

# Build Docker image
build_image() {
    echo "🔨 Building Docker image..."
    docker build -t ai-mentor:latest .
    echo -e "${GREEN}✅ Image built successfully${NC}"
}

# Deploy with Docker Compose
deploy_compose() {
    echo "🐳 Starting services with Docker Compose..."
    
    if [ "$ENVIRONMENT" == "production" ]; then
        # Update nginx.conf with actual domain
        sed -i "s/your-domain.com/$DOMAIN/g" nginx.conf
        
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml up -d
        
        echo -e "${GREEN}✅ Production deployment complete${NC}"
        echo "📌 Services running:"
        docker-compose -f docker-compose.prod.yml ps
    else
        docker-compose down
        docker-compose up -d
        
        echo -e "${GREEN}✅ Staging deployment complete${NC}"
        echo "📌 Services running:"
        docker-compose ps
    fi
}

# Health check
health_check() {
    echo "🏥 Running health check..."
    sleep 5
    
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is healthy${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        echo "Check logs with: docker-compose logs web"
        exit 1
    fi
}

# SSL Setup (production only)
setup_ssl() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return
    fi
    
    echo "🔒 Setting up SSL with Let's Encrypt..."
    
    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot..."
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Get SSL certificate
    sudo certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN
    
    echo -e "${GREEN}✅ SSL certificate obtained${NC}"
}

# Main deployment flow
main() {
    check_requirements
    build_image
    
    if [ "$ENVIRONMENT" == "production" ]; then
        setup_ssl
    fi
    
    deploy_compose
    health_check
    
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo ""
    echo "📝 Next steps:"
    if [ "$ENVIRONMENT" == "production" ]; then
        echo "  1. Your app is available at: https://$DOMAIN"
        echo "  2. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
        echo "  3. View stats: docker stats"
    else
        echo "  1. Your app is available at: http://localhost:8000"
        echo "  2. Monitor logs: docker-compose logs -f"
        echo "  3. View stats: docker stats"
    fi
}

# Run main function
main