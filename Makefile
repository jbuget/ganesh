.PHONY: install check lint test db-up db-down migrate dev-server dev-client

install:
	$(MAKE) -C server install
	cd client && pnpm install

db-up:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	$(MAKE) -C server migrate

lint:
	$(MAKE) -C server lint
	cd client && pnpm lint && pnpm format:check && pnpm type-check

test:
	$(MAKE) -C server test
	cd client && pnpm test

check: lint test

dev-server:
	$(MAKE) -C server run

dev-client:
	cd client && pnpm dev
