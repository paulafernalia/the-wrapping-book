# Set default path (can be overridden)
POST_OUTPUT_DIR := ./instagram
TUTORIAL_INPUT_DIR := ./tutorials

book:
	uv run generate_book.py

post:
	@read -p "Enter carry name as it appears on tutorial file: " carryname; \
	uv run generate_post.py $(POST_OUTPUT_DIR) $$carryname

black:
	uv tool run black **/*.py


make extract-steps:
	@read -p "Enter carry name as it appears on tutorial file: " carryname; \
	uv run extract_tutorial_steps.py $(TUTORIAL_INPUT_DIR) $$carryname
