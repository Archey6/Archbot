# Archbot

Work in progress personal project bot

# Setup
- Token is stored in an environment variable `bot_token`
- SQLite3 Database name is stored in `utils/database.py`
- `python3.6 run.py` to start bot

# Commands 

##### Moderation:
`** Is Admin Only`
###### Parent aliases apply to sub commands
#
| Command       | Alias    | Parameter  | Function |
| ------------- |-------------|-----|--------|
|** Blacklist     | bl, ignore | User | Ignores all commands passed by a user|
|** Prefix    | pf    |  Prefix String| Sets the bot prefix; Server specific|
| ** Prefix Delete | remove, del| None |Sets bot prefix back to default; Server specific |
|** Command | cmd | Command Name/Alias | Disables this command server wide |
|** Command User | None | Command, User | Disables this command for specific user server wide


#### Tags:
| Command | Alias | Parameter | Function|
|---------|-------|-----------|---------|
|Tag      | t     | Tag Name  | Displays tag contents|
|Add| create |Tag Name, Content | Adds a tag with specified name and content|
|Remove| del, delete| Tag Name | Deletes specified tag, if owned by user passing the command
|Edit | change| Tag Name, New Content | Edits specified tag's content
|Owner| creator | Tag Name | Displays owner of specified tag|
|List| None | User(optional) | Displays users tags; If no user displays tags of user who invoked the command
| Search | find | Tag Name(wildcard)| Find all tags when name similar to the one specified|
|Search Content | | Content | Finds all tags with similar content 




