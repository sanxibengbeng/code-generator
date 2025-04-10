.PHONY: env run clean

# Create and set up virtual environment
env:
	python3 -m venv venv
	source venv/bin/activate && pip install --upgrade pip
	source venv/bin/activate && pip install -r requirements.txt
	@echo "Virtual environment created and dependencies installed."
	@echo "Run 'make run' to start the application."

# Run the application
run:
	source venv/bin/activate && python app.py

# Clean up generated files and cache
clean:
	rm -rf __pycache__
	rm -rf uploads/*
	rm -rf generated/*
	@echo "Cleaned up cache and generated files."