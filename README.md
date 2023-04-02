# Telegram Bot for Expense Management

This Telegram bot helps you manage your expenses by allowing you to track and set daily expenses, 
and also generate a report. Below is a list of commands that the bot accepts:

Commands:
- ```/set_day_expense```: sets the expense for a specific date.
- ```/get_report```: generates a report with daily expenses and sends it as a file.
- ```/recalculate_monthly_budged```: allows you to update the monthly budget.
- ```/start``` or ```/reprint```: prints the current monthly budget and daily expenses.

To use this bot go to telegram and search for ```@my_wallet02_bot``` or [click here](https://t.me/my_wallet02_bot).


### Installation

Clone the repository:shell
```shell
$ git clone https://github.com/ThaisBarrosAlvim/expenses_tracker_bot
```

Create a virtual environment and activate it:shell
```shell
$ python -m venv env
$ source env/bin/activate
```

Install the required packages:ruby
```shell
$ pip install -r requirements.txt
```

Create a ```.env``` file in the root directory and add the following line:
```env
BOT_TOKEN=YOUR_BOT_TOKEN
```

Run the bot:
```shell
$ python main.py
```
