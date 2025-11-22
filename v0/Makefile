.PHONY: help build up down restart logs logs-follow ps health clean

help: ## Show this help message
	@echo "Sentinell - Victim Environment Management"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all victim services
	@echo "Building victim services..."
	docker-compose build

up: ## Start the victim cluster
	@echo "Starting victim cluster..."
	docker-compose up -d
	@echo ""
	@echo "Victim cluster is starting..."
	@echo "Frontend: http://localhost"
	@echo "Product API: http://localhost:8000"
	@echo "Payment Service: http://localhost:3002"
	@echo "PostgreSQL: localhost:5432"

down: ## Stop the victim cluster
	@echo "Stopping victim cluster..."
	docker-compose down

restart: ## Restart the victim cluster
	@echo "Restarting victim cluster..."
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs

logs-follow: ## Follow logs from all services
	docker-compose logs -f

ps: ## Show running containers
	docker-compose ps

health: ## Check health status of all services
	@echo "Checking service health..."
	@echo ""
	@echo "Frontend:"
	@curl -s http://localhost:3000 > /dev/null && echo "  ✓ Healthy" || echo "  ✗ Down"
	@echo ""
	@echo "Product API:"
	@curl -s http://localhost:8000/health | grep -q "healthy" && echo "  ✓ Healthy" || echo "  ✗ Down"
	@echo ""
	@echo "Payment Service:"
	@curl -s http://localhost:3002/health | grep -q "healthy" && echo "  ✓ Healthy" || echo "  ✗ Down"
	@echo ""
	@echo "PostgreSQL:"
	@docker-compose exec -T postgres pg_isready -U admin > /dev/null 2>&1 && echo "  ✓ Healthy" || echo "  ✗ Down"
	@echo ""
	@echo "Nginx:"
	@curl -s http://localhost > /dev/null && echo "  ✓ Healthy" || echo "  ✗ Down"

clean: ## Stop and remove all containers, volumes, and images
	@echo "Cleaning up victim cluster..."
	docker-compose down -v --rmi all
	@echo "Cleanup complete!"

dev: build up ## Build and start the victim cluster
	@echo ""
	@echo "Victim cluster is ready!"
	@echo "Access the application at: http://localhost"
