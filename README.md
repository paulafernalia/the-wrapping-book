# The Wrapping Book

**The Wrapping Book** is a Python project that generates a PDF book with wrapping tutorials. It programmatically creates the book from data and images stored in a Supabase database, which can be accessed through your Supabase instance. This project is also used in [The Wrapping Gallery](https://www.thewrappinggallery.com).

## Features
- Generate a PDF containing a series of babywearing tutorials, each with a cover and a step-by-step tutorial
- Retrieve data and images from Supabase.
- Organize tutorials into sections for easy reference (TODO)
- Add some FAQ, preface and other bits (TODO)

## Installation

To get started with **The Wrapping Book**, follow the installation steps below:

## Prerequisites

Ensure you have the following software installed:
- Python 3.8 or higher
- [`uv`](https://github.com/astral-sh/uv): a fast Python package manager (used instead of `pip`)
- `make`

## Usage

Start by cloning the repository to your local machine:

```bash
git clone https://github.com/your-username/the-wrapping-book.git
cd the-wrapping-book
```

Create a `.env` file in the root directory and add the following variables:
```bash
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name
```

Generate the book* by running:
```bash
make book
```
* This takes all carries in the database marked as having a tutorial and it assumes a cover in SVG exists in `covers/` for these carries.

Generate a post* by running:
```
make post
```
* This assumes the steps exist in AWS S3 and a cover in SVG exists in `covers/`

Extract steps from a tutorial (pdf file) and upload them to AWS S3 (also mark tutorial as available in table in supabase) with:
```
make extract-steps
```

Autoformat code with
```
make black
```
