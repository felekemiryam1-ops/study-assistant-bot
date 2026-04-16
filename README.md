# AI Study Assistant Bot

An AI-powered Telegram bot that quizzes you on your study materials.

## What it does
- Upload any PDF, PowerPoint or Word document
- AI generates 10 quiz questions from your content
- Bot quizzes you one question at a time
- Explains wrong answers based on your file
- Shows your final score

## Tech Stack
- Python
- Anthropic Claude AI
- AWS Lambda (serverless compute)
- AWS API Gateway (webhook handler)
- AWS S3 (file storage)
- AWS Secrets Manager (secure credentials)
- AWS CloudWatch (monitoring and logs)
- Telegram Bot API

## Architecture
User → Telegram → API Gateway → Lambda → Claude AI → Response

## How to run locally
1. Clone the repo
2. Install dependencies: pip install -r requirements.txt
3. Add your keys to .env file
4. Run: python3 bot.py
