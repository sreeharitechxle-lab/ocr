# Business Card Extraction Logic

This project now uses a specialized extraction module (`extraction.py`) to parse business card details.

## Features
Extracts the following fields:
- **Name**: Uses heuristics to identify the mostly likely name (capitalized, 2+ words, context).
- **Job Title**: Matches against a dictionary of common titles.
- **Company**: Identifies companies by suffixes (`Inc`, `LLC`, `Ltd`, `Company`, `&`).
- **Email**: Standard Regex.
- **Phone**: Improved Regex `(?:(?:\+|00)[\s.-]{0,3})?(?:\d[\s.-]{0,3}){7,15}`.
- **Address**: Locates addresses via keywords (`Street`, `Road`) or Zip Code validation.
- **Website**: Extracts URLs.

## How to Customize
You can modify `extraction.py` to add more rules:
- **Add Job Titles**: Update the `job_titles` list.
- **Add Company Suffixes**: Update `company_suffixes`.
- **Address Keywords**: Add local terms to `address_keywords`.

## Testing
Run `python test_extraction.py` to see the logic applied to sample text.
