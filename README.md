# Discord Giveaway Bot

An advanced Discord bot for managing giveaways with features like automatic winner selection, multiple concurrent giveaways, and customizable requirements.

## Features

- Multiple concurrent giveaways
- Automatic winner selection
- Participant tracking
- Role-based entry requirements
- Embed-based messages
- Reaction-based entry system
- Reroll functionality
- Force end giveaways
- List active giveaways

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with your Discord bot token:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

3. Run the bot:
```bash
python bot.py
```

## Commands

### Basic Commands

- `!giveaway [minutes] [prize]` - Create a new giveaway
  - Example: `!giveaway 60 Nintendo Switch`
  - Creates a giveaway lasting 60 minutes for a Nintendo Switch prize

- `!list` - List all active giveaways
  - Shows all current giveaways with their end times and required roles

- `!end [message_id]` - Force end a giveaway
  - Ends the giveaway immediately and selects a winner
  - Example: `!end 1234567890`

- `!reroll [message_id]` - Reroll a giveaway winner
  - Selects a new random winner from participants
  - Example: `!reroll 1234567890`

### Advanced Features

- Role Requirements
  - Add role requirements to limit who can enter
  - Example: `!giveaway 60 Nintendo Switch @Member @Premium`
  - Users must have at least one of the specified roles to enter

- Blacklist
  - Add specific users to a blacklist
  - Blacklisted users cannot enter the giveaway
  - Example: `!giveaway 60 Nintendo Switch @1234567890`

- Multiple Giveaways
  - Run multiple giveaways simultaneously
  - Each giveaway has its own entry system and winner selection

- Automatic Entry Validation
  - Automatically removes reactions from users who don't meet requirements
  - Sends notifications to users explaining why they can't enter
  - Shows required roles and blacklist status in error messages

## How to Use

1. Creating a Giveaway
   ```
   !giveaway 60 Nintendo Switch @Member @Premium @1234567890
   ```
   - Duration: 60 minutes
   - Prize: Nintendo Switch
   - Required Roles: Member or Premium
   - Blacklisted Users: 1234567890
   - Users must have at least one of the required roles to enter

2. Entering Giveaways
   - React with 🎉 to the giveaway message
   - The bot will automatically track your entry
   - You'll receive a DM when you enter successfully

3. Managing Giveaways
   - Use `!list` to see all active giveaways
   - Use `!end [message_id]` to force end a giveaway
   - Use `!reroll [message_id]` to select a new winner

## Requirements

- Python 3.8+
- Discord.py
- Python-dotenv
- Other dependencies listed in requirements.txt

## Tips

- Always specify a clear prize name
- Set appropriate duration for your giveaways
- Use role requirements to control who can enter
- Add users to blacklist to prevent specific users from entering
- Keep track of message IDs for managing giveaways
- Use both roles and blacklist together for maximum control
