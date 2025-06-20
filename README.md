# Easy-Email

Easy-Email is an AI assistant that helps you generate and send emails professionally. It uses the GPT-3.5 model to generate email content and utilizes Gmail, Outlook, and other email APIs to send emails directly through the application, saving time and improving efficiency.

## Contents

[Installation](#installation)

## Installation

1. Clone the repository

    ```bash
    git clone https://github.com/Daryan97/Easy-Email
    ```

1. Install the required packages using pip

    ```plaintext
    pip install -r requirements.txt
    ```

1. Deploy the Redis server

    ```yaml
    version: '3'
    services:
    redis:
        image: redis
        ports:
        - "6379:6379"
        command: ["redis-server", "--requirepass", "your_password"]
    ```

1. Configure the environment variables

    ```plaintext
    cp .env.example .env
    ```

1. Create the database with the same name as in the `.env` file

1. Run the development server

    ```plaintext
    flask run
    ```
