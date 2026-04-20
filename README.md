# AI Study Assistant Bot

An AI-powered Telegram bot that quizzes you on your study materials using Claude AI.

## What it does
- Upload any PDF, PowerPoint or Word document
- AI generates 10 quiz questions from your content
- Bot quizzes you one question at a time
- Explains wrong answers based on your actual file
- Shows your final score

## Architecture

User → Telegram → API Gateway → Lambda 1 → SQS Queue
                                                ↓
                                           Lambda 2
                                                ↓
                                          Claude AI
                                                ↓
                                          DynamoDB
                                                ↓
                                        Answer to User

## AWS Services Used
- Lambda — serverless compute for bot logic
- API Gateway — receives Telegram webhook
- SQS — decouples file processing from webhook handling
- DynamoDB — stores quiz sessions between Lambda functions
- S3 — stores deployment packages
- Secrets Manager — secure API key storage
- CloudWatch — monitoring and logging
- IAM — permissions and security

## Tech Stack
- Python 3.11
- Anthropic Claude AI
- AWS Lambda, API Gateway, SQS, DynamoDB, S3
- GitHub Actions CI/CD

## How to run locally
1. Clone the repo
2. Install dependencies: pip install -r requirements.txt
3. Add your keys to .env file
4. Run: python3 bot.py

## CI/CD
Every push to main automatically deploys to AWS via GitHub Actions.

## Features coming soon
- Difficulty levels (Easy, Medium, Hard)
- Flashcard mode
- Multiple languages including Amharic
- Score history
- Leaderboard
