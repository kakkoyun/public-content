# GopherCon UK 2025 - Demo Sync Makefile
# 
# This Makefile syncs demo content from the gopherconuk25-demo repository
# into the local demo directory for presentation preparation.

# Variables
HOME_DIR := $(HOME)
DEMO_SRC := $(HOME_DIR)/Workspace/Projects/Open-Source/Misc/gopherconuk25-demo
DEMO_DEST := ./demo

# Default target
.PHONY: help
help:
	@echo "GopherCon UK 2025 Demo Sync Utilities"
	@echo "====================================="
	@echo "Available targets:"
	@echo "  sync-demo    - Sync demo content from external repository"
	@echo "  clean-demo   - Clean demo directory"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Source: $(DEMO_SRC)"
	@echo "Destination: $(DEMO_DEST)"

# Sync demo content
.PHONY: sync-demo
sync-demo:
	@echo "🚀 Syncing GopherCon UK 2025 demo content..."
	@echo "Source: $(DEMO_SRC)"
	@echo "Destination: $(DEMO_DEST)"
	@mkdir -p "$(DEMO_DEST)"
	@if [ ! -d "$(DEMO_SRC)" ]; then \
		echo "❌ Error: Source directory does not exist: $(DEMO_SRC)"; \
		echo "   Make sure the gopherconuk25-demo repository is cloned to the expected location."; \
		exit 1; \
	fi
	@rsync -avz --delete \
		--exclude='.git' \
		--exclude='.DS_Store' \
		--exclude='*.swp' \
		--exclude='*.tmp' \
		--exclude='.gitignore' \
		--exclude='node_modules' \
		--exclude='vendor' \
		--exclude='*.log' \
		--progress \
		"$(DEMO_SRC)/" "$(DEMO_DEST)/"
	@echo "✅ Demo sync complete!"
	@echo "📁 Demo files are now available in: $(DEMO_DEST)"

# Clean demo directory
.PHONY: clean-demo
clean-demo:
	@echo "🧹 Cleaning demo directory..."
	@if [ -d "$(DEMO_DEST)" ]; then \
		rm -rf "$(DEMO_DEST)"; \
		echo "✅ Demo directory cleaned"; \
	else \
		echo "ℹ️  Demo directory doesn't exist"; \
	fi

# Show demo directory contents
.PHONY: list-demo
list-demo:
	@echo "📂 Demo directory contents:"
	@if [ -d "$(DEMO_DEST)" ]; then \
		ls -la "$(DEMO_DEST)"; \
	else \
		echo "❌ Demo directory doesn't exist. Run 'make sync-demo' first."; \
	fi